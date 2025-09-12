document.addEventListener('DOMContentLoaded', () => {
    const originalTextarea = document.getElementById('original-text');
    const alteredTextarea = document.getElementById('altered-text');
    const compareBtn = document.getElementById('compare-btn');
    const diffOriginalOutput = document.getElementById('diff-original-output');
    const diffAlteredOutput = document.getElementById('diff-altered-output');
    const diffSummary = document.querySelector('.diff-summary');
    const removalsCount = document.getElementById('removals-count');
    const additionsCount = document.getElementById('additions-count');
    const linesOriginalCount = document.getElementById('lines-original-count');
    const linesAlteredCount = document.getElementById('lines-altered-count');
    const copyOriginalBtn = document.getElementById('copy-original-btn');
    const copyAlteredBtn = document.getElementById('copy-altered-btn');
    const themeToggleBtn = document.getElementById('theme-toggle');

    // Função para renderizar o diff lado a lado
    function renderDiff(diffData) {
        diffOriginalOutput.innerHTML = '';
        diffAlteredOutput.innerHTML = '';
        diffSummary.style.display = 'flex';

        function createLineElement(line) {
            const lineDiv = document.createElement('div');
            lineDiv.classList.add('diff-line', line.type);
            
            const lineNumSpan = document.createElement('span');
            lineNumSpan.className = 'line-num';
            lineNumSpan.textContent = line.line_num;

            const lineContentSpan = document.createElement('span');
            lineContentSpan.className = 'line-content';
            
            // ATUALIZAÇÃO: Envolve o conteúdo em um span para a máscara de fundo
            const content = line.content.replace(/ /g, '&nbsp;') || '&nbsp;';
            lineContentSpan.innerHTML = `<span class="text-wrapper">${content}</span>`;

            lineDiv.appendChild(lineNumSpan);
            lineDiv.appendChild(lineContentSpan);
            return lineDiv;
        }

        diffData.diff_lines_original.forEach(line => {
            diffOriginalOutput.appendChild(createLineElement(line));
        });

        diffData.diff_lines_altered.forEach(line => {
            diffAlteredOutput.appendChild(createLineElement(line));
        });

        // Atualizar resumo
        if (diffData.diff_type === "JSON/Objeto") {
             removalsCount.textContent = ``;
             additionsCount.textContent = ``;
             linesOriginalCount.textContent = 'JSON Diff';
             linesAlteredCount.textContent = '';
        } else {
            removalsCount.textContent = `${diffData.summary.removals} remoções`;
            additionsCount.textContent = `${diffData.summary.additions} adições`;
            linesOriginalCount.textContent = `${diffData.summary.total_lines_original} linhas`;
            linesAlteredCount.textContent = `${diffData.summary.total_lines_altered} linhas`;
        }
    }

    // Função para chamar a API de comparação
    async function findDifference() {
        compareBtn.disabled = true;
        diffOriginalOutput.innerHTML = '<div class="diff-line context"><span class="line-num"></span><span class="line-content">Comparando...</span></div>';
        diffAlteredOutput.innerHTML = '<div class="diff-line context"><span class="line-num"></span><span class="line-content">Comparando...</span></div>';
        diffSummary.style.display = 'none';

        try {
            const response = await fetch('/api/compare', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    original: originalTextarea.value,
                    altered: alteredTextarea.value
                }),
            });

            if (!response.ok) {
                throw new Error(`Erro na API: ${response.statusText}`);
            }

            const result = await response.json();
            renderDiff(result);

        } catch (error) {
            diffOriginalOutput.innerHTML = `<div class="diff-line removed"><span class="line-num"></span><span class="line-content">Ocorreu um erro: ${error.message}</span></div>`;
            diffAlteredOutput.innerHTML = '';
            diffSummary.style.display = 'none';
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

    // Função de copiar para a área de transferência
    function copyToClipboard(element) {
        const textToCopy = element.value;
        navigator.clipboard.writeText(textToCopy).then(() => {
            alert('Conteúdo copiado para a área de transferência!');
        }).catch(err => {
            console.error('Falha ao copiar:', err);
        });
    }

    copyOriginalBtn.addEventListener('click', () => copyToClipboard(originalTextarea));
    copyAlteredBtn.addEventListener('click', () => copyToClipboard(alteredTextarea));
});