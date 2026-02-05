"""
Script simples para validar a estrutura do section_templates.json
"""
import json
import os

def validate_templates():
    """Valida que o JSON está bem formado e tem a estrutura esperada"""
    
    # Carrega o JSON
    template_path = os.path.join(os.path.dirname(__file__), "section_templates.json")
    
    with open(template_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print("✅ JSON carregado com sucesso!\n")
    
    # Valida estrutura
    assert "meta" in data, "Falta seção 'meta'"
    assert "templates" in data, "Falta seção 'templates'"
    assert "global_guidelines" in data, "Falta seção 'global_guidelines'"
    
    print("✅ Estrutura principal válida\n")
    
    # Valida cada seção
    sections = data["templates"]
    expected_sections = ["intro", "mercado", "empresa", "financials", "transacao", "pontos_aprofundar"]
    
    for section_name in expected_sections:
        assert section_name in sections, f"Falta seção {section_name}"
        section = sections[section_name]
        
        # Verifica que tem examples
        assert "examples" in section, f"Seção {section_name} não tem 'examples'"
        examples = section["examples"]
        
        # Conta exemplos
        num_examples = len(examples)
        print(f"📋 Seção '{section_name}': {num_examples} exemplo(s)")
        
        # Valida estrutura de cada exemplo
        for i, ex in enumerate(examples, 1):
            assert "context" in ex, f"Exemplo {i} da seção {section_name} sem 'context'"
            assert "text" in ex, f"Exemplo {i} da seção {section_name} sem 'text'"
            print(f"   - Exemplo {i}: {ex['context'][:50]}...")
    
    print("\n✅ Todas as 6 seções têm estrutura válida!")
    
    # Estatísticas finais
    total_examples = sum(len(sections[s]["examples"]) for s in expected_sections)
    print(f"\n📊 Total: {total_examples} exemplos distribuídos em {len(expected_sections)} seções")
    
    # Verifica diversidade
    print("\n📈 Diversidade de exemplos:")
    for section_name in expected_sections:
        contexts = [ex["context"] for ex in sections[section_name]["examples"]]
        print(f"   {section_name}: {', '.join(contexts)}")

if __name__ == "__main__":
    try:
        validate_templates()
        print("\n🎉 Validação completa! Todos os testes passaram.")
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        raise
