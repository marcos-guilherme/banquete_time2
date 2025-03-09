"""
Funções utilitárias para o projeto.
"""

def load_prompt(path: str) -> str:
    """
    Carrega um arquivo de prompt e retorna seu conteúdo como string.
    
    Args:
        path: Caminho para o arquivo de prompt
        
    Returns:
        O conteúdo do arquivo como string
    """
    try:
        with open(path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        raise Exception(f"Erro ao carregar o prompt de {path}: {str(e)}") 