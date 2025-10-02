// JS extraído de base.html para auto-dismiss y secuenciación de alertas
(function(){
    const AUTO_DISMISS_MS = 3000; // 3 segundos por defecto
    const FIRST_MSG = 'Procesamiento creado. Iniciando...';
    const SECOND_MSG = 'Procesamiento en segundo plano iniciado. Visualizando resultados...';

    function scheduleAutoDismiss(elem, delay){
        setTimeout(()=>{
            elem.classList.add('auto-alert-hidden');
            setTimeout(()=> elem.remove(), 350);
        }, delay);
    }

    document.addEventListener('DOMContentLoaded', ()=>{
        const alerts = Array.from(document.querySelectorAll('.container .alert'));
        if(!alerts || alerts.length===0) return;

        alerts.forEach((a, idx)=>{
            a.classList.add('auto-alert', 'auto-alert-slide');
            setTimeout(()=> a.classList.add('show'), 80 * idx);
        });

        const firstAlert = alerts.find(a => (a.textContent||'').includes(FIRST_MSG));
        const secondAlert = alerts.find(a => (a.textContent||'').includes(SECOND_MSG));

        if(firstAlert){
            scheduleAutoDismiss(firstAlert, AUTO_DISMISS_MS);
        }

        if(secondAlert){
            if(firstAlert){
                secondAlert.classList.add('auto-alert-hidden');
                setTimeout(()=>{
                    secondAlert.classList.remove('auto-alert-hidden');
                    secondAlert.classList.add('show');
                    scheduleAutoDismiss(secondAlert, AUTO_DISMISS_MS);
                }, AUTO_DISMISS_MS + 220);
            } else {
                scheduleAutoDismiss(secondAlert, AUTO_DISMISS_MS);
            }
        }

        alerts.forEach(a=>{
            const txt = a.textContent || '';
            if(![FIRST_MSG, SECOND_MSG].some(p=> txt.includes(p))){
                scheduleAutoDismiss(a, AUTO_DISMISS_MS + 400);
            }
        });
    });
})();
