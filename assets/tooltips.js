window.dashMantineFunctions = window.dashMantineFunctions || {};

window.dashMantineFunctions.renderVariableOptionWithTooltip = function({ option, checked }) {
    var React = window.React || React;
    if (!React) {
        return option.label;
    }
    return React.createElement(
        'div',
        {
            title: option.tooltip || '',
            style: {
                width: '100%',
                padding: '4px 8px',
                cursor: 'pointer',
                whiteSpace: 'normal',
                fontSize: '13px'
            }
        },
        option.label
    );
};

window.dashMantineFunctions.renderIndicatorOption = function({ option, checked }) {
    var React = window.React || React;
    if (!React) {
        return option.label;
    }
    
    var subtitle = '';
    if (option.value === 'INCI') {
        subtitle = ' (nombre de nouveaux cas sur la période 2021-2023)';
    } else if (option.value === 'PREV') {
        subtitle = ' (nombre de cas en 2022)';
    }
    
    if (subtitle) {
        return React.createElement(
            'div',
            {
                style: {
                    display: 'flex',
                    alignItems: 'baseline',
                    flexWrap: 'wrap',
                    gap: '4px'
                }
            },
            React.createElement('span', { style: { fontWeight: 500 } }, option.label),
            React.createElement('span', {
                style: {
                    fontSize: '11px',
                    fontStyle: 'italic',
                    color: '#868e96'
                }
            }, subtitle)
        );
    }
    
    return option.label;
};
