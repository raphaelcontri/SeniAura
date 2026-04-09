if (!window.dash_clientside) {
    window.dash_clientside = {};
}
window.dash_clientside.clientside = {
    scrollToAccordion: function (n_clicks) {
        if (n_clicks) {
            const el = document.getElementById('accordion-item-prise-en-main');
            if (el) {
                // scrollIntoView will respect the scroll-margin-top defined in CSS
                el.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        }
        return window.dash_clientside.no_update;
    },
    scrollToElement: function (n_clicks, elementId) {
        if (n_clicks) {
            const el = document.getElementById(elementId);
            if (el) {
                el.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        }
        return window.dash_clientside.no_update;
    },
    scrollToRadar: function (n_clicks) {
        if (n_clicks) {
            const el = document.getElementById('container-radar');
            if (el) {
                el.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        }
        return window.dash_clientside.no_update;
    }
};
