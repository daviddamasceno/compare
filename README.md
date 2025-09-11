## 📦 Versionamento e CI/CD

### Controle de Versão

A versão da aplicação é controlada pelo arquivo `VERSION` na raiz do projeto. Cada vez que o pipeline de CI/CD é executado na branch `main`, ele constrói a imagem Docker e a marca com duas tags:

1.  `latest`: Apontando para a versão mais recente da branch `main`.
2.  A versão especificada no arquivo `VERSION` (ex: `1.0.0`).

Para lançar uma nova versão, simplesmente atualize o número no arquivo `VERSION`, faça o commit e envie para a branch `main`.

### Execução Manual do Pipeline

Além dos gatilhos automáticos, é possível executar o pipeline de publicação manualmente:

1.  Navegue até a aba **Actions** do repositório.
2.  Selecione o workflow **"Publicar Imagem Docker"**.
3.  Clique no botão **"Run workflow"**.
4.  Selecione a branch desejada e confirme a execução.

Isso é útil para re-construir uma imagem ou testar o fluxo de CI/CD sem a necessidade de um novo commit.