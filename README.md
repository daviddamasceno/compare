# Compare - Ferramenta de Diff Online

[![GitHub Actions Workflow](https://github.com/daviddamasceno/compare/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/daviddamasceno/compare/actions/workflows/docker-publish.yml)
[![Docker Hub](https://img.shields.io/docker/pulls/damascenod/compare)](https://hub.docker.com/r/damascenod/compare)

**Compare** é uma ferramenta web simples e poderosa para comparar textos e estruturas de dados como JSON. A aplicação é construída com um backend Python (Flask) e um frontend moderno em JavaScript, totalmente containerizada com Docker.

Acesse a interface limpa e intuitiva, cole seus dados e veja as diferenças instantaneamente.

![Screenshot da Aplicação](https://i.imgur.com/GjT8Z7i.png)

## ✨ Features

* **Comparação Inteligente:** Detecta automaticamente se o conteúdo é JSON para uma comparação estrutural ou se é texto plano para uma comparação linha a linha (diff).
* **Interface Web Moderna:** Frontend reativo construído com HTML, CSS e JavaScript puros.
* **Tema Claro e Escuro:** Adapta-se automaticamente ao tema do seu sistema e permite a troca manual.
* **Containerizado:** Empacotado com Docker para fácil execução e portabilidade.
* **CI/CD Automatizado:** Imagens Docker são construídas e publicadas no [Docker Hub](https://hub.docker.com/r/damascenod/compare) automaticamente via GitHub Actions.

## 🛠️ Stack Tecnológica

* **Backend:** Python 3.11, Flask, Gunicorn
* **Frontend:** HTML5, CSS3, JavaScript (Vanilla)
* **Lógica de Comparação:** `difflib` e `DeepDiff`
* **Containerização:** Docker, Docker Compose

## 🚀 Como Executar

A aplicação foi projetada para ser executada via Docker, garantindo um ambiente consistente e sem complicações.

### Pré-requisitos

* [Docker](https://www.docker.com/products/docker-desktop/) instalado e em execução.

### Executando com Docker Compose (Recomendado)

O Docker Compose é a maneira mais simples de subir a aplicação localmente.

1.  Clone este repositório:
    ```bash
    git clone [https://github.com/daviddamasceno/compare.git](https://github.com/daviddamasceno/compare.git)
    cd compare
    ```

2.  Suba o serviço:
    ```bash
    docker-compose up --build
    ```

3.  Acesse a aplicação no seu navegador:
    [**http://localhost:8000**](http://localhost:8000)

### Executando com comandos Docker (Alternativa)

Você também pode construir e executar a imagem manualmente.

1.  Construa a imagem Docker:
    ```bash
    docker build -t damascenod/compare .
    ```

2.  Execute o container:
    ```bash
    docker run -p 8000:8000 --name compare-app damascenod/compare
    ```

3.  Acesse a aplicação no seu navegador:
    [**http://localhost:8000**](http://localhost:8000)

## ⚙️ CI/CD

Este repositório utiliza **GitHub Actions** para automatizar o processo de build e publicação da imagem Docker.

* **Gatilhos:** O workflow é acionado em cada `push` para a branch `main` (gerando a tag `latest`) e em cada `push` de uma tag Git no formato `v*.*.*` (ex: `v1.0.0`).
* **Publicação:** As imagens são enviadas para o repositório público do Docker Hub: [damascenod/compare](https://hub.docker.com/r/damascenod/compare).