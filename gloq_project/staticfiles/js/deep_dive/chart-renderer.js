// Chart Renderer - Handles all natal chart visualization
class ChartRenderer {
    constructor() {
        this.currentNatalChart = null;
        this.tooltipElement = null;
        this.init();
    }

    init() {
        this.createTooltipElement();
    }

    setChartData(natalChart) {
        this.currentNatalChart = natalChart;
    }

    createTooltipElement() {
        // Create tooltip if it doesn't exist
        if (!document.getElementById('chart-tooltip')) {
            const tooltip = document.createElement('div');
            tooltip.id = 'chart-tooltip';
            tooltip.innerHTML = `
                <div class="tooltip-header">
                    <span id="tooltip-icon"></span>
                    <span id="tooltip-title"></span>
                </div>
                <div class="tooltip-divider"></div>
                <div class="tooltip-body" id="tooltip-content"></div>
            `;
            document.body.appendChild(tooltip);
        }
        this.tooltipElement = document.getElementById('chart-tooltip');
    }

    // Main rendering function
    renderChartWheel(natalChart, containerId, size = 600, isFullView = false) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.error('Container not found:', containerId);
            return;
        }

        this.currentNatalChart = natalChart;
        container.classList.add('has-data');
        const center = size / 2;

        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.setAttribute('viewBox', `0 0 ${size} ${size}`);
        svg.setAttribute('class', 'w-full h-full');

        // Conversion helpers
        const astroToSVGAngle = (longitude) => {
            return (180 - longitude) * Math.PI / 180;
        };

        const getCirclePosition = (longitude, radius) => {
            const angle = astroToSVGAngle(longitude);
            return {
                x: center + radius * Math.cos(angle),
                y: center - radius * Math.sin(angle)
            };
        };

        // Create conjunction glow filter
        this.createConjunctionGlowFilter(svg);

        // Draw layers
        this.drawZodiacRing(svg, center, size);

        if (natalChart.houses && natalChart.houses.length > 0) {
            this.drawHouses(svg, center, natalChart.houses, getCirclePosition);
        }

        if (natalChart.aspects && natalChart.aspects.length > 0) {
            this.drawAspects(svg, center, natalChart.planets, natalChart.aspects, getCirclePosition);
        }

        this.drawPlanets(svg, center, natalChart.planets, getCirclePosition, isFullView);

        if (natalChart.ascendant) {
            this.drawAscendant(svg, center, natalChart.ascendant, getCirclePosition);
        }

        container.innerHTML = '';
        container.appendChild(svg);
    }

    createConjunctionGlowFilter(svg) {
        const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
        
        const filter = document.createElementNS('http://www.w3.org/2000/svg', 'filter');
        filter.setAttribute('id', 'conjunction-glow');
        filter.setAttribute('x', '-50%');
        filter.setAttribute('y', '-50%');
        filter.setAttribute('width', '200%');
        filter.setAttribute('height', '200%');
        
        const feGaussianBlur = document.createElementNS('http://www.w3.org/2000/svg', 'feGaussianBlur');
        feGaussianBlur.setAttribute('in', 'SourceGraphic');
        feGaussianBlur.setAttribute('stdDeviation', '2');
        feGaussianBlur.setAttribute('result', 'blur');
        
        const feMerge = document.createElementNS('http://www.w3.org/2000/svg', 'feMerge');
        
        const feMergeNode1 = document.createElementNS('http://www.w3.org/2000/svg', 'feMergeNode');
        feMergeNode1.setAttribute('in', 'blur');
        
        const feMergeNode2 = document.createElementNS('http://www.w3.org/2000/svg', 'feMergeNode');
        feMergeNode2.setAttribute('in', 'SourceGraphic');
        
        feMerge.appendChild(feMergeNode1);
        feMerge.appendChild(feMergeNode2);
        filter.appendChild(feGaussianBlur);
        filter.appendChild(feMerge);
        defs.appendChild(filter);
        svg.appendChild(defs);
    }

    drawZodiacRing(svg, center, size) {
        const outerRadius = size / 2 - 10;
        const innerRadius = outerRadius - 30;

        const zodiacSigns = [
            { name: 'Aries', symbol: '♈', start: 0, element: 'Fire', modality: 'Cardinal' },
            { name: 'Taurus', symbol: '♉', start: 30, element: 'Earth', modality: 'Fixed' },
            { name: 'Gemini', symbol: '♊', start: 60, element: 'Air', modality: 'Mutable' },
            { name: 'Cancer', symbol: '♋', start: 90, element: 'Water', modality: 'Cardinal' },
            { name: 'Leo', symbol: '♌', start: 120, element: 'Fire', modality: 'Fixed' },
            { name: 'Virgo', symbol: '♍', start: 150, element: 'Earth', modality: 'Mutable' },
            { name: 'Libra', symbol: '♎', start: 180, element: 'Air', modality: 'Cardinal' },
            { name: 'Scorpio', symbol: '♏', start: 210, element: 'Water', modality: 'Fixed' },
            { name: 'Sagittarius', symbol: '♐', start: 240, element: 'Fire', modality: 'Mutable' },
            { name: 'Capricorn', symbol: '♑', start: 270, element: 'Earth', modality: 'Cardinal' },
            { name: 'Aquarius', symbol: '♒', start: 300, element: 'Air', modality: 'Fixed' },
            { name: 'Pisces', symbol: '♓', start: 330, element: 'Water', modality: 'Mutable' }
        ];

        // Outer circle
        const outerCircle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        outerCircle.setAttribute('cx', center);
        outerCircle.setAttribute('cy', center);
        outerCircle.setAttribute('r', outerRadius);
        outerCircle.setAttribute('fill', 'none');
        outerCircle.setAttribute('stroke', 'rgba(99, 102, 241, 0.3)');
        outerCircle.setAttribute('stroke-width', '2');
        svg.appendChild(outerCircle);

        // Inner circle
        const innerCircle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        innerCircle.setAttribute('cx', center);
        innerCircle.setAttribute('cy', center);
        innerCircle.setAttribute('r', innerRadius);
        innerCircle.setAttribute('fill', 'none');
        innerCircle.setAttribute('stroke', 'rgba(99, 102, 241, 0.2)');
        innerCircle.setAttribute('stroke-width', '1');
        svg.appendChild(innerCircle);

        const self = this;

        zodiacSigns.forEach(sign => {
            const startAngle = (180 - sign.start) * Math.PI / 180;
            const midAngle = (180 - (sign.start + 15)) * Math.PI / 180;

            // Division lines
            const lineStart = {
                x: center + innerRadius * Math.cos(startAngle),
                y: center - innerRadius * Math.sin(startAngle)
            };
            const lineEnd = {
                x: center + outerRadius * Math.cos(startAngle),
                y: center - outerRadius * Math.sin(startAngle)
            };

            const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            line.setAttribute('x1', lineStart.x);
            line.setAttribute('y1', lineStart.y);
            line.setAttribute('x2', lineEnd.x);
            line.setAttribute('y2', lineEnd.y);
            line.setAttribute('stroke', 'rgba(99, 102, 241, 0.2)');
            line.setAttribute('stroke-width', '1');
            svg.appendChild(line);

            // Zodiac symbol
            const symbolRadius = (outerRadius + innerRadius) / 2;
            const symbolPos = {
                x: center + symbolRadius * Math.cos(midAngle),
                y: center - symbolRadius * Math.sin(midAngle)
            };

            const signGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
            signGroup.style.cursor = 'pointer';

            const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            text.setAttribute('x', symbolPos.x);
            text.setAttribute('y', symbolPos.y);
            text.setAttribute('text-anchor', 'middle');
            text.setAttribute('dominant-baseline', 'central');
            text.setAttribute('fill', 'rgba(129, 140, 248, 0.6)');
            text.setAttribute('font-size', '18');
            text.setAttribute('font-weight', 'bold');
            text.textContent = sign.symbol;

            signGroup.appendChild(text);

            // Hover effects
            signGroup.addEventListener('mouseenter', function (e) {
                text.setAttribute('fill', 'rgba(129, 140, 248, 1)');
                text.setAttribute('font-size', '22');
                self.showTooltip(e, 'zodiac', sign);
            });

            signGroup.addEventListener('mousemove', function (e) {
                self.updateTooltipPosition(e);
            });

            signGroup.addEventListener('mouseleave', function () {
                text.setAttribute('fill', 'rgba(129, 140, 248, 0.6)');
                text.setAttribute('font-size', '18');
                self.hideTooltip();
            });

            svg.appendChild(signGroup);
        });
    }

    drawHouses(svg, center, houses, getCirclePosition) {
        const houseRadius = center - 50;

        houses.forEach(house => {
            const pos = getCirclePosition(house.longitude, houseRadius);

            const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            line.setAttribute('x1', center);
            line.setAttribute('y1', center);
            line.setAttribute('x2', pos.x);
            line.setAttribute('y2', pos.y);
            line.setAttribute('stroke', house.house_number === 1 || house.house_number === 10
                ? 'rgba(168, 85, 247, 0.4)'
                : 'rgba(148, 163, 184, 0.2)');
            line.setAttribute('stroke-width', house.house_number === 1 || house.house_number === 10 ? '2' : '1');
            line.setAttribute('stroke-dasharray', '2,2');
            svg.appendChild(line);

            const labelPos = getCirclePosition(house.longitude, houseRadius - 20);
            const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            text.setAttribute('x', labelPos.x);
            text.setAttribute('y', labelPos.y);
            text.setAttribute('text-anchor', 'middle');
            text.setAttribute('dominant-baseline', 'central');
            text.setAttribute('fill', 'rgba(148, 163, 184, 0.5)');
            text.setAttribute('font-size', '10');
            text.textContent = house.house_number;
            svg.appendChild(text);
        });
    }

    drawAspects(svg, center, planets, aspects, getCirclePosition) {
        const aspectRadius = center - 80;
        const planetRadius = center - 70;
        
        const aspectStyles = {
            'Conjunction': { color: 'rgba(255, 215, 0, 0.9)', width: 4, dasharray: 'none' },
            'Opposition': { color: 'rgba(239, 68, 68, 0.5)', width: 2, dasharray: 'none' },
            'Trine': { color: 'rgba(34, 197, 94, 0.5)', width: 2, dasharray: 'none' },
            'Square': { color: 'rgba(251, 146, 60, 0.5)', width: 2, dasharray: 'none' },
            'Sextile': { color: 'rgba(59, 130, 246, 0.4)', width: 1.5, dasharray: 'none' }
        };

        const self = this;

        aspects.forEach(aspect => {
            const planet1 = planets.find(p => p.name === aspect.planet1);
            const planet2 = planets.find(p => p.name === aspect.planet2);

            if (!planet1 || !planet2) return;

            const style = aspectStyles[aspect.aspect_type] || {
                color: 'rgba(148, 163, 184, 0.3)',
                width: 1,
                dasharray: 'none'
            };

            // Special handling for Conjunctions - draw as curved arc
            if (aspect.aspect_type === 'Conjunction') {
                const pos1 = getCirclePosition(planet1.longitude, planetRadius);
                const pos2 = getCirclePosition(planet2.longitude, planetRadius);
                
                const dx = pos2.x - pos1.x;
                const dy = pos2.y - pos1.y;
                const distance = Math.sqrt(dx * dx + dy * dy);
                
                if (distance < 50) {
                    // Very close conjunction - simple curved arc
                    const midX = (pos1.x + pos2.x) / 2;
                    const midY = (pos1.y + pos2.y) / 2;
                    
                    const toCenterX = center - midX;
                    const toCenterY = center - midY;
                    const toCenterLen = Math.sqrt(toCenterX * toCenterX + toCenterY * toCenterY);
                    
                    const offsetX = midX - (toCenterX / toCenterLen) * 50;
                    const offsetY = midY - (toCenterY / toCenterLen) * 50;
                    
                    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
                    const d = `M ${pos1.x} ${pos1.y} Q ${offsetX} ${offsetY} ${pos2.x} ${pos2.y}`;
                    
                    path.setAttribute('d', d);
                    path.setAttribute('stroke', style.color);
                    path.setAttribute('stroke-width', style.width);
                    path.setAttribute('fill', 'none');
                    path.setAttribute('stroke-linecap', 'round');
                    path.setAttribute('class', 'aspect-line conjunction-arc');
                    path.style.cursor = 'pointer';
                    path.setAttribute('filter', 'url(#conjunction-glow)');
                    
                    this.addAspectInteractions(path, aspect, style);
                    svg.appendChild(path);
                    
                } else {
                    // Wider conjunction - circular arc
                    let angle1 = (180 - planet1.longitude);
                    let angle2 = (180 - planet2.longitude);
                    
                    if (angle1 < 0) angle1 += 360;
                    if (angle2 < 0) angle2 += 360;
                    
                    let angleDiff = angle2 - angle1;
                    if (angleDiff > 180) angleDiff -= 360;
                    if (angleDiff < -180) angleDiff += 360;
                    
                    const largeArcFlag = Math.abs(angleDiff) > 180 ? 1 : 0;
                    const sweepFlag = angleDiff > 0 ? 0 : 1;
                    const arcRadius = planetRadius + 50;
                    
                    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
                    const d = `M ${pos1.x} ${pos1.y} A ${arcRadius} ${arcRadius} 0 ${largeArcFlag} ${sweepFlag} ${pos2.x} ${pos2.y}`;
                    
                    path.setAttribute('d', d);
                    path.setAttribute('stroke', style.color);
                    path.setAttribute('stroke-width', style.width);
                    path.setAttribute('fill', 'none');
                    path.setAttribute('stroke-linecap', 'round');
                    path.setAttribute('class', 'aspect-line conjunction-arc');
                    path.style.cursor = 'pointer';
                    path.setAttribute('filter', 'url(#conjunction-glow)');
                    
                    this.addAspectInteractions(path, aspect, style);
                    svg.appendChild(path);
                }
                
                // Add endpoint markers
                const marker1 = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
                marker1.setAttribute('cx', pos1.x);
                marker1.setAttribute('cy', pos1.y);
                marker1.setAttribute('r', 4);
                marker1.setAttribute('fill', style.color);
                marker1.setAttribute('class', 'conjunction-marker');
                marker1.style.pointerEvents = 'none';

                const marker2 = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
                marker2.setAttribute('cx', pos2.x);
                marker2.setAttribute('cy', pos2.y);
                marker2.setAttribute('r', 4);
                marker2.setAttribute('fill', style.color);
                marker2.setAttribute('class', 'conjunction-marker');
                marker2.style.pointerEvents = 'none';

                svg.appendChild(marker1);
                svg.appendChild(marker2);

            } else {
                // Normal aspect lines
                const pos1 = getCirclePosition(planet1.longitude, aspectRadius);
                const pos2 = getCirclePosition(planet2.longitude, aspectRadius);

                const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
                line.setAttribute('x1', pos1.x);
                line.setAttribute('y1', pos1.y);
                line.setAttribute('x2', pos2.x);
                line.setAttribute('y2', pos2.y);
                line.setAttribute('stroke', style.color);
                line.setAttribute('stroke-width', style.width);
                line.setAttribute('class', 'aspect-line');
                line.style.cursor = 'pointer';

                if (style.dasharray !== 'none') {
                    line.setAttribute('stroke-dasharray', style.dasharray);
                }

                this.addAspectInteractions(line, aspect, style);
                svg.appendChild(line);
            }
        });
    }

    addAspectInteractions(element, aspect, style) {
        const self = this;
        
        element.addEventListener('mouseenter', function (e) {
            element.setAttribute('stroke-width', parseFloat(style.width) + 2);
            if (aspect.aspect_type === 'Conjunction') {
                element.setAttribute('stroke', 'rgba(255, 215, 0, 1)');
            }
            self.showTooltip(e, 'aspect', aspect);
        });

        element.addEventListener('mousemove', function (e) {
            self.updateTooltipPosition(e);
        });

        element.addEventListener('mouseleave', function () {
            element.setAttribute('stroke-width', style.width);
            element.setAttribute('stroke', style.color);
            self.hideTooltip();
        });
    }

    drawPlanets(svg, center, planets, getCirclePosition, isFullView = false) {
        const planetRadius = center - 70;
        const self = this;

        planets.forEach(planet => {
            const pos = getCirclePosition(planet.longitude, planetRadius);

            const group = document.createElementNS('http://www.w3.org/2000/svg', 'g');
            group.setAttribute('class', 'planet-group');
            if (isFullView) {
                group.style.cursor = 'pointer';
            }

            const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
            circle.setAttribute('cx', pos.x);
            circle.setAttribute('cy', pos.y);
            circle.setAttribute('r', isFullView ? 16 : 12);
            circle.setAttribute('fill', 'rgba(30, 41, 59, 0.9)');
            circle.setAttribute('stroke', 'rgba(129, 140, 248, 0.5)');
            circle.setAttribute('stroke-width', '1.5');
            group.appendChild(circle);

            const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            text.setAttribute('x', pos.x);
            text.setAttribute('y', pos.y);
            text.setAttribute('text-anchor', 'middle');
            text.setAttribute('dominant-baseline', 'central');
            text.setAttribute('fill', '#fff');
            text.setAttribute('font-size', isFullView ? '18' : '14');
            text.setAttribute('pointer-events', 'none');
            text.textContent = planet.symbol;
            group.appendChild(text);

            if (isFullView) {
                group.addEventListener('mouseenter', function (e) {
                    circle.setAttribute('fill', 'rgba(99, 102, 241, 0.8)');
                    circle.setAttribute('r', 18);
                    self.showTooltip(e, 'planet', planet);
                });

                group.addEventListener('mousemove', function (e) {
                    self.updateTooltipPosition(e);
                });

                group.addEventListener('mouseleave', function () {
                    circle.setAttribute('fill', 'rgba(30, 41, 59, 0.9)');
                    circle.setAttribute('r', 16);
                    self.hideTooltip();
                });

                group.addEventListener('click', function (event) {
                    event.stopPropagation();
                    self.showPlanetInfo(planet);
                });
            }

            svg.appendChild(group);
        });
    }

    drawAscendant(svg, center, ascendant, getCirclePosition) {
        const ascLongitude = this.signToLongitude(ascendant.sign, ascendant.degree);
        const pos = getCirclePosition(ascLongitude, center - 40);

        const marker = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        marker.setAttribute('x', pos.x);
        marker.setAttribute('y', pos.y);
        marker.setAttribute('text-anchor', 'middle');
        marker.setAttribute('dominant-baseline', 'central');
        marker.setAttribute('fill', 'rgba(168, 85, 247, 0.9)');
        marker.setAttribute('font-size', '12');
        marker.setAttribute('font-weight', 'bold');
        marker.textContent = 'ASC';
        svg.appendChild(marker);
    }

    signToLongitude(sign, degree) {
        const signs = {
            'Aries': 0, 'Taurus': 30, 'Gemini': 60, 'Cancer': 90,
            'Leo': 120, 'Virgo': 150, 'Libra': 180, 'Scorpio': 210,
            'Sagittarius': 240, 'Capricorn': 270, 'Aquarius': 300, 'Pisces': 330
        };
        return signs[sign] + degree;
    }

    // Tooltip methods
    showTooltip(event, type, data) {
        if (!this.tooltipElement) return;

        const icon = document.getElementById('tooltip-icon');
        const title = document.getElementById('tooltip-title');
        const content = document.getElementById('tooltip-content');

        if (type === 'planet') {
            icon.textContent = data.symbol;
            title.textContent = data.name;
            content.innerHTML = `
                <div><span class="tooltip-label">Sign:</span> <span class="tooltip-value">${data.sign} ${data.degree.toFixed(2)}°</span></div>
                <div><span class="tooltip-label">Element:</span> <span class="tooltip-value">${data.element}</span></div>
                <div><span class="tooltip-label">House:</span> <span class="tooltip-value">${data.house || 'N/A'}</span></div>
                ${data.retrograde ? '<div class="tooltip-label" style="color: #fca5a5; margin-top: 4px;">⟲ Retrograde</div>' : ''}
            `;
        } else if (type === 'aspect') {
            const aspectIcons = {
                'Conjunction': '☌',
                'Opposition': '☍',
                'Trine': '△',
                'Square': '□',
                'Sextile': '⚹'
            };
            const aspectDescriptions = {
                'Conjunction': 'Blending of energies',
                'Opposition': 'Tension and balance',
                'Trine': 'Harmonious flow',
                'Square': 'Dynamic challenge',
                'Sextile': 'Opportunity and ease'
            };
            icon.textContent = aspectIcons[data.aspect_type] || '⚹';
            title.textContent = data.aspect_type;
            content.innerHTML = `
                <div><span class="tooltip-value">${data.planet1}</span> to <span class="tooltip-value">${data.planet2}</span></div>
                <div><span class="tooltip-label">Orb:</span> <span class="tooltip-value">${data.orb.toFixed(2)}°</span></div>
                <div class="tooltip-label" style="margin-top: 6px;">${aspectDescriptions[data.aspect_type]}</div>
            `;
        } else if (type === 'zodiac') {
            icon.textContent = data.symbol;
            title.textContent = data.name;
            content.innerHTML = `
                <div><span class="tooltip-label">Element:</span> <span class="tooltip-value">${data.element}</span></div>
                <div><span class="tooltip-label">Modality:</span> <span class="tooltip-value">${data.modality}</span></div>
                <div><span class="tooltip-label">Degrees:</span> <span class="tooltip-value">${data.start}° - ${data.start + 30}°</span></div>
            `;
        }

        this.tooltipElement.classList.add('visible');
        this.updateTooltipPosition(event);
    }

    updateTooltipPosition(event) {
        if (!this.tooltipElement) return;

        const tooltipRect = this.tooltipElement.getBoundingClientRect();
        const offset = 20;

        let x = event.clientX + offset;
        let y = event.clientY + offset;

        if (x + tooltipRect.width > window.innerWidth) {
            x = event.clientX - tooltipRect.width - offset;
        }
        if (y + tooltipRect.height > window.innerHeight) {
            y = event.clientY - tooltipRect.height - offset;
        }

        this.tooltipElement.style.left = x + 'px';
        this.tooltipElement.style.top = y + 'px';
    }

    hideTooltip() {
        if (this.tooltipElement) {
            this.tooltipElement.classList.remove('visible');
        }
    }

    showPlanetInfo(planet) {
        const infoContainer = document.getElementById('planet-info');
        const infoContent = document.getElementById('planet-info-content');

        if (!infoContainer || !infoContent) {
            console.warn('Planet info panel not found');
            return;
        }

        // Find aspects involving this planet
        const planetAspects = this.currentNatalChart.aspects.filter(
            aspect => aspect.planet1 === planet.name || aspect.planet2 === planet.name
        );

        const elementDescriptions = {
            'Fire': 'Dynamic, passionate, action-oriented',
            'Earth': 'Practical, grounded, material-focused',
            'Air': 'Intellectual, communicative, social',
            'Water': 'Emotional, intuitive, sensitive'
        };

        const planetMeanings = {
            'Sun': 'Core identity, ego, vitality, life purpose',
            'Moon': 'Emotions, instincts, inner self, needs',
            'Mercury': 'Communication, thinking, intellect, learning',
            'Venus': 'Love, beauty, values, relationships',
            'Mars': 'Action, desire, energy, assertiveness',
            'Jupiter': 'Growth, expansion, luck, wisdom',
            'Saturn': 'Structure, discipline, responsibility, karma',
            'Uranus': 'Innovation, rebellion, sudden change',
            'Neptune': 'Dreams, spirituality, illusion, compassion',
            'Pluto': 'Transformation, power, death/rebirth'
        };

        infoContent.innerHTML = `
            <div class="space-y-4">
                <div class="flex items-center justify-between pb-3 border-b border-indigo-500/30">
                    <div class="flex items-center gap-3">
                        <span class="text-3xl">${planet.symbol}</span>
                        <div>
                            <h5 class="text-xl font-bold text-white">${planet.name}</h5>
                            <p class="text-sm text-slate-400">${planetMeanings[planet.name] || 'Celestial body'}</p>
                        </div>
                    </div>
                </div>

                <div class="grid grid-cols-2 gap-3">
                    <div class="bg-slate-700/30 rounded-lg p-3">
                        <span class="text-xs text-slate-400 block mb-1">Sign</span>
                        <span class="text-indigo-300 font-semibold">${planet.sign} ${planet.degree.toFixed(2)}°</span>
                    </div>
                    <div class="bg-slate-700/30 rounded-lg p-3">
                        <span class="text-xs text-slate-400 block mb-1">Element</span>
                        <span class="text-white font-semibold">${planet.element}</span>
                    </div>
                    <div class="bg-slate-700/30 rounded-lg p-3">
                        <span class="text-xs text-slate-400 block mb-1">Longitude</span>
                        <span class="text-white font-semibold">${planet.longitude.toFixed(2)}°</span>
                    </div>
                    <div class="bg-slate-700/30 rounded-lg p-3">
                        <span class="text-xs text-slate-400 block mb-1">House</span>
                        <span class="text-white font-semibold">${planet.house ? 'House ' + planet.house : 'N/A'}</span>
                    </div>
                </div>

                ${planet.retrograde ? `
                    <div class="bg-red-900/20 border border-red-500/30 rounded-lg p-3">
                        <span class="text-red-400 font-semibold">
                            <i class="fas fa-undo mr-2"></i>Retrograde Motion
                        </span>
                        <p class="text-xs text-slate-300 mt-1">
                            This planet appears to move backward, suggesting internalized or review energy.
                        </p>
                    </div>
                ` : ''}

                <div class="bg-gradient-to-r from-indigo-900/20 to-purple-900/20 rounded-lg p-3 border border-indigo-500/20">
                    <span class="text-xs text-slate-400 block mb-1">Element Quality</span>
                    <p class="text-sm text-slate-200">${elementDescriptions[planet.element]}</p>
                </div>

                ${planetAspects.length > 0 ? `
                    <div>
                        <h6 class="text-sm font-semibold text-slate-300 mb-2 flex items-center">
                            <i class="fas fa-project-diagram text-pink-400 mr-2"></i>
                            Aspects (${planetAspects.length})
                        </h6>
                        <div class="space-y-2 max-h-40 overflow-y-auto custom-scrollbar">
                            ${planetAspects.map(aspect => {
                                const otherPlanet = aspect.planet1 === planet.name ? aspect.planet2 : aspect.planet1;
                                const aspectColors = {
                                    'Conjunction': 'text-yellow-300',
                                    'Opposition': 'text-red-400',
                                    'Trine': 'text-green-400',
                                    'Square': 'text-orange-400',
                                    'Sextile': 'text-blue-400'
                                };
                                const aspectIcons = {
                                    'Conjunction': '☌',
                                    'Opposition': '☍',
                                    'Trine': '△',
                                    'Square': '□',
                                    'Sextile': '⚹'
                                };
                                return `
                                    <div class="bg-slate-700/30 rounded-lg p-2 flex items-center justify-between hover:bg-slate-700/50 transition-colors">
                                        <span class="text-sm">
                                            <span class="${aspectColors[aspect.aspect_type]} font-bold mr-2">
                                                ${aspectIcons[aspect.aspect_type]}
                                            </span>
                                            <span class="text-slate-300">${aspect.aspect_type} to ${otherPlanet}</span>
                                        </span>
                                        <span class="text-xs text-slate-400">${aspect.orb.toFixed(1)}°</span>
                                    </div>
                                `;
                            }).join('')}
                        </div>
                    </div>
                ` : '<p class="text-sm text-slate-400 italic">No major aspects</p>'}
            </div>
        `;

        infoContainer.classList.remove('hidden');
    }
}

// Initialize global instance
window.chartRenderer = new ChartRenderer();