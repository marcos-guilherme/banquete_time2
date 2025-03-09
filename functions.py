
#Carrega um prompt a partir de um arquivo, para que o Agente saiba o que fazer. 
def load_prompt(prompt_path: str) -> str:
    with open(prompt_path, "r") as f:
        return f.read()




