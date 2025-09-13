document.addEventListener('DOMContentLoaded', () => {
    const originalTextarea = document.getElementById('original-text');
    const alteredTextarea = document.getElementById('altered-text');
    const compareBtn = document.getElementById('compare-btn');
    const propertiesSwitch = document.getElementById('properties-switch');
    const diffDisplayGrid = document.querySelector('.diff-display-grid');
    const diffOriginalOutput = document.getElementById('diff-original-output');
    const diffAlteredOutput = document.getElementById('diff-altered-output');
    const diffSummary = document.querySelector('.diff-summary');
    const removalsCount = document.getElementById('removals-count');
    const additionsCount = document.getElementById('additions-count');
    const changesCount = document.getElementById('changes-count');
    const linesOriginalCount = document.getElementById('lines-original-count');
    const linesAlteredCount = document.getElementById('lines-altered-count');
    const copyOriginalBtn = document.getElementById('copy-original-btn');
    const copyAlteredBtn = document.getElementById('copy-altered-btn');
    const themeToggleBtn = document.getElementById('theme-toggle');

    function createLineElement(line) {
        const lineDiv = document.createElement('div');
        lineDiv.classList.add('diff-line', line.type);
        const lineNumSpan = document.createElement('span');
        lineNumSpan.className = 'line-num';
        lineNumSpan.textContent = line.line_num;
        const lineContentSpan = document.createElement('span');
        lineContentSpan.className = 'line-content';
        const content = line.content.replace(/ /g, '&nbsp;') || '&nbsp;';
        lineContentSpan.innerHTML = `<span class="text-wrapper">${content}</span>`;
        lineDiv.appendChild(lineNumSpan);
        lineDiv.appendChild(lineContentSpan);
        return lineDiv;
    }

    function renderDiff(diffData) {
        diffOriginalOutput.innerHTML = '';
        diffAlteredOutput.innerHTML = '';
        diffSummary.style.display = 'flex';
        if (diffData.diff_type === "Texto") {
            diffDisplayGrid.style.gridTemplateColumns = '1fr 1fr';
            diffData.diff_lines_original.forEach(line => { diffOriginalOutput.appendChild(createLineElement(line)); });
            diffData.diff_lines_altered.forEach(line => { diffAlteredOutput.appendChild(createLineElement(line)); });
        } else {
            diffDisplayGrid.style.gridTemplateColumns = '1fr';
            const line = diffData.diff_lines_original[0] || { content: 'Nenhuma diferença encontrada.' };
            const preElement = document.createElement('pre');
            preElement.textContent = line.content;
            diffOriginalOutput.appendChild(preElement);
            diffAlteredOutput.innerHTML = '';
        }
        const summary = diffData.summary || {};
        const removals = summary.removals ?? 0;
        const additions = summary.additions ?? 0;
        const changes = summary.changes ?? 0;
        removalsCount.textContent = `${removals} remoções`;
        additionsCount.textContent = `${additions} adições`;
        if (changes > 0) {
            changesCount.textContent = `${changes} alterações`;
            changesCount.style.display = 'inline';
        } else {
            changesCount.style.display = 'none';
        }
        if (diffData.diff_type === "Texto") {
            linesOriginalCount.textContent = `${summary.total_lines_original} linhas`;
            linesAlteredCount.textContent = `${summary.total_lines_altered} linhas`;
            linesOriginalCount.style.display = 'inline';
            linesAlteredCount.style.display = 'inline';
        } else {
            linesOriginalCount.style.display = 'none';
            linesAlteredCount.style.display = 'none';
        }
    }

    async function findDifference() {
        compareBtn.disabled = true;
        diffSummary.style.display = 'none';
        diffOriginalOutput.innerHTML = '<div class="diff-line context"><span class="line-content">Comparando...</span></div>';
        diffAlteredOutput.innerHTML = '';

        const isProperties = propertiesSwitch.checked;

        try {
            const response = await fetch('/api/compare', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    original: originalTextarea.value,
                    altered: alteredTextarea.value,
                    is_properties: isProperties
                }),
            });
            if (!response.ok) { throw new Error(`Erro na API: ${response.statusText}`); }
            const result = await response.json();
            renderDiff(result);
        } catch (error) {
            diffOriginalOutput.innerHTML = `<div class="diff-line removed"><span class="line-content">Ocorreu um erro: ${error.message}</span></div>`;
            diffAlteredOutput.innerHTML = '';
            diffSummary.style.display = 'none';
        } finally {
            compareBtn.disabled = false;
        }
    }

    compareBtn.addEventListener('click', findDifference);
    const currentTheme = localStorage.getItem('theme');
    if (currentTheme) { document.body.classList.add(currentTheme); } 
    else if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
        document.body.classList.add('dark-mode');
    }
    themeToggleBtn.addEventListener('click', () => {
        document.body.classList.toggle('dark-mode');
        let theme = document.body.classList.contains('dark-mode') ? 'dark-mode' : '';
        localStorage.setItem('theme', theme);
    });
    function copyToClipboard(element) {
        navigator.clipboard.writeText(element.value)
            .then(() => alert('Conteúdo copiado para a área de transferência!'))
            .catch(err => console.error('Falha ao copiar:', err));
    }
    copyOriginalBtn.addEventListener('click', () => copyToClipboard(originalTextarea));
    copyAlteredBtn.addEventListener('click', () => copyToClipboard(alteredTextarea));
});