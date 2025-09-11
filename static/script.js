document.addEventListener('DOMContentLoaded', () => {
    const originalText = document.getElementById('original-text');
    const alteredText = document.getElementById('altered-text');
    const compareBtn = document.getElementById('compare-btn');
    const resultOutput = document.getElementById('result-output');
    const diffTypeSpan = document.getElementById('diff-type');
    const themeToggleBtn = document.getElementById('theme-toggle');

    // Função para chamar a API de comparação
    async function findDifference() {
        compareBtn.disabled = true;
        resultOutput.textContent = 'Comparando...';
        diffTypeSpan.textContent = '';

        try {
            const response = await fetch('/api/compare', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    original: originalText.value,
                    altered: alteredText.value
                }),
            });

            if (!response.ok) {
                throw new Error(`Erro na API: ${response.statusText}`);
            }

            const result = await response.json();
            resultOutput.textContent = result.diff;
            diffTypeSpan.textContent = result.type;

        } catch (error) {
            resultOutput.textContent = `Ocorreu um erro: ${error.message}`;
        } finally {
            compareBtn.disabled = false;
        }
    }

    compareBtn.addEventListener('click', findDifference);

    // Lógica para o tema escuro/claro
    const currentTheme = localStorage.getItem('theme');
    if (currentTheme) {
        document.body.classList.add(currentTheme);
    } else if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
        document.body.classList.add('dark-mode');
    }

    themeToggleBtn.addEventListener('click', () => {
        document.body.classList.toggle('dark-mode');
        let theme = document.body.classList.contains('dark-mode') ? 'dark-mode' : '';
        localStorage.setItem('theme', theme);
    });
});