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

        // Draw layers (order matters for z-index)
        this.drawZodiacRing(svg, center, size);

        // Draw house segment fills for Whole Sign (subtle background)
        if (natalChart.houses && natalChart.houses.length > 0) {
            this.drawHouseSegments(svg, center, natalChart.houses, getCirclePosition);
        }

        if (natalChart.houses && natalChart.houses.length > 0) {
            this.drawHouses(svg, center, natalChart.houses, getCirclePosition);
        }

        if (natalChart.aspects && natalChart.aspects.length > 0) {
            this.drawAspects(svg, center, natalChart.planets, natalChart.aspects, getCirclePosition);
        }

        this.drawPlanets(svg, center, natalChart.planets, getCirclePosition, isFullView);

        // Draw Ascendant and Midheaven markers
        if (natalChart.ascendant) {
            this.drawAscendant(svg, center, natalChart.ascendant, getCirclePosition);
        }

        if (natalChart.midheaven) {
            this.drawMidheaven(svg, center, natalChart.midheaven, getCirclePosition);
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

    drawHouseSegments(svg, center, houses, getCirclePosition) {
        const segmentOuterRadius = center - 40;
        const segmentInnerRadius = center - 130;

        // Check if we have planets_in_houses data
        const planetsInHouses = this.currentNatalChart?.planets_in_houses || {};

        houses.forEach(house => {
            const houseNum = house.number;
            const startLon = house.cusp_longitude;
            const endLon = houses[(houseNum % 12)].cusp_longitude;
            
            const startAngle = (180 - startLon) * Math.PI / 180;
            const endAngle = (180 - endLon) * Math.PI / 180;
            
            const startOuter = {
                x: center + segmentOuterRadius * Math.cos(startAngle),
                y: center - segmentOuterRadius * Math.sin(startAngle)
            };
            const endOuter = {
                x: center + segmentOuterRadius * Math.cos(endAngle),
                y: center - segmentOuterRadius * Math.sin(endAngle)
            };
            const startInner = {
                x: center + segmentInnerRadius * Math.cos(startAngle),
                y: center - segmentInnerRadius * Math.sin(startAngle)
            };
            const endInner = {
                x: center + segmentInnerRadius * Math.cos(endAngle),
                y: center - segmentInnerRadius * Math.sin(endAngle)
            };
            
            let angleDiff = (startLon - endLon + 360) % 360;
            const largeArcFlag = angleDiff > 180 ? 1 : 0;
            
            const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
            const d = `
                M ${startOuter.x} ${startOuter.y}
                A ${segmentOuterRadius} ${segmentOuterRadius} 0 ${largeArcFlag} 0 ${endOuter.x} ${endOuter.y}
                L ${endInner.x} ${endInner.y}
                A ${segmentInnerRadius} ${segmentInnerRadius} 0 ${largeArcFlag} 1 ${startInner.x} ${startInner.y}
                Z
            `;
            
            path.setAttribute('d', d);
            
            const hasPlanets = planetsInHouses[houseNum] && planetsInHouses[houseNum].length > 0;
            
            if (hasPlanets) {
                path.setAttribute('fill', 'rgba(99, 102, 241, 0.08)');
                path.setAttribute('stroke', 'rgba(99, 102, 241, 0.15)');
                path.setAttribute('stroke-width', '0.5');
            } else {
                path.setAttribute('fill', 'rgba(99, 102, 241, 0.02)');
                path.setAttribute('stroke', 'none');
            }
            
            path.style.pointerEvents = 'none';
            svg.appendChild(path);
        });
    }

    drawHouses(svg, center, houses, getCirclePosition) {
        const houseRadius = center - 50;
        const self = this;

        const signAbbrev = {
            'Aries': 'Ari', 'Taurus': 'Tau', 'Gemini': 'Gem', 'Cancer': 'Can',
            'Leo': 'Leo', 'Virgo': 'Vir', 'Libra': 'Lib', 'Scorpio': 'Sco',
            'Sagittarius': 'Sag', 'Capricorn': 'Cap', 'Aquarius': 'Aqu', 'Pisces': 'Pis'
        };

        const romanNumerals = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X', 'XI', 'XII'];

        houses.forEach(house => {
            const pos = getCirclePosition(house.cusp_longitude, houseRadius);

            const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            line.setAttribute('x1', center);
            line.setAttribute('y1', center);
            line.setAttribute('x2', pos.x);
            line.setAttribute('y2', pos.y);
            
            line.setAttribute('stroke', house.number === 1 || house.number === 10
                ? 'rgba(168, 85, 247, 0.4)'
                : 'rgba(148, 163, 184, 0.2)');
            line.setAttribute('stroke-width', house.number === 1 || house.number === 10 ? '2' : '1');
            line.setAttribute('stroke-dasharray', '2,2');
            svg.appendChild(line);

            // Enhanced house labels with Roman numerals
            const labelRadius = houseRadius - 25;
            
            const nextHouse = houses[house.number % 12];
            const nextCusp = nextHouse.cusp_longitude;
            
            let midLongitude = (house.cusp_longitude + nextCusp) / 2;
            
            if (Math.abs(nextCusp - house.cusp_longitude) > 180) {
                midLongitude = ((house.cusp_longitude + nextCusp + 360) / 2) % 360;
            }
            
            const midPos = getCirclePosition(midLongitude, labelRadius);
            
            const labelGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
            labelGroup.style.cursor = 'pointer';
            
            // Rounded rectangle background for house label
            const bgRect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
            bgRect.setAttribute('x', midPos.x - 22);
            bgRect.setAttribute('y', midPos.y - 12);
            bgRect.setAttribute('width', '44');
            bgRect.setAttribute('height', '24');
            bgRect.setAttribute('rx', '4');
            bgRect.setAttribute('ry', '4');
            bgRect.setAttribute('fill', 'rgba(15, 23, 42, 0.9)');
            bgRect.setAttribute('stroke', 'rgba(148, 163, 184, 0.4)');
            bgRect.setAttribute('stroke-width', '1');
            labelGroup.appendChild(bgRect);
            
            // Roman numeral (larger and centered)
            const houseNum = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            houseNum.setAttribute('x', midPos.x);
            houseNum.setAttribute('y', midPos.y - 1);
            houseNum.setAttribute('text-anchor', 'middle');
            houseNum.setAttribute('dominant-baseline', 'central');
            houseNum.setAttribute('fill', 'rgba(203, 213, 225, 0.9)');
            houseNum.setAttribute('font-size', '11');
            houseNum.setAttribute('font-weight', '600');
            houseNum.setAttribute('font-family', 'serif');
            houseNum.textContent = romanNumerals[house.number - 1];
            labelGroup.appendChild(houseNum);
            
            // Sign abbreviation (smaller, below)
            const signText = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            signText.setAttribute('x', midPos.x);
            signText.setAttribute('y', midPos.y + 9);
            signText.setAttribute('text-anchor', 'middle');
            signText.setAttribute('dominant-baseline', 'central');
            signText.setAttribute('fill', 'rgba(148, 163, 184, 0.6)');
            signText.setAttribute('font-size', '7');
            signText.textContent = signAbbrev[house.sign] || house.sign.substring(0, 3);
            labelGroup.appendChild(signText);
            
            labelGroup.addEventListener('mouseenter', function(e) {
                bgRect.setAttribute('fill', 'rgba(30, 41, 59, 0.95)');
                bgRect.setAttribute('stroke', 'rgba(99, 102, 241, 0.6)');
                houseNum.setAttribute('font-size', '12');
                
                const planetsInHouse = self.currentNatalChart?.planets_in_houses?.[house.number] || [];
                
                self.showTooltip(e, 'house', {
                    number: house.number,
                    sign: house.sign,
                    degree: house.degree,
                    planets: planetsInHouse
                });
            });
            
            labelGroup.addEventListener('mousemove', function(e) {
                self.updateTooltipPosition(e);
            });
            
            labelGroup.addEventListener('mouseleave', function() {
                bgRect.setAttribute('fill', 'rgba(15, 23, 42, 0.9)');
                bgRect.setAttribute('stroke', 'rgba(148, 163, 184, 0.4)');
                houseNum.setAttribute('font-size', '11');
                self.hideTooltip();
            });
            
            svg.appendChild(labelGroup);
        });
    }

    drawAspects(svg, center, planets, aspects, getCirclePosition) {
        const aspectRadius = center - 80;
        const planetRadius = center - 70;
        
        // Define planet importance weights (higher = more important)
        const planetWeights = {
            'Sun': 10, 'Moon': 10, 'Mercury': 8, 'Venus': 8, 'Mars': 8,
            'Jupiter': 7, 'Saturn': 7, 'Uranus': 5, 'Neptune': 5, 'Pluto': 5,
            'Chiron': 3, 'Lilith': 2, 'North Node': 1, 'South Node': 1
        };
        
        const getAspectWeight = (planet1Name, planet2Name) => {
            const weight1 = planetWeights[planet1Name] || 1;
            const weight2 = planetWeights[planet2Name] || 1;
            return (weight1 + weight2) / 2;
        };
        
        const aspectStyles = {
            'Conjunction': { baseColor: 'rgba(255, 215, 0, 0.9)', baseWidth: 5, dasharray: 'none' },
            'Opposition': { baseColor: 'rgba(239, 68, 68, 0.5)', baseWidth: 2.5, dasharray: 'none' },
            'Trine': { baseColor: 'rgba(34, 197, 94, 0.5)', baseWidth: 2.5, dasharray: 'none' },
            'Square': { baseColor: 'rgba(251, 146, 60, 0.5)', baseWidth: 2.5, dasharray: 'none' },
            'Sextile': { baseColor: 'rgba(59, 130, 246, 0.4)', baseWidth: 2, dasharray: 'none' }
        };

        const self = this;

        aspects.forEach(aspect => {
            const planet1 = planets.find(p => p.name === aspect.planet1);
            const planet2 = planets.find(p => p.name === aspect.planet2);

            if (!planet1 || !planet2) return;

            // Calculate aspect importance based on planets involved
            const aspectWeight = getAspectWeight(aspect.planet1, aspect.planet2);
            const weightMultiplier = Math.max(0.2, aspectWeight / 10); // Normalize with minimum
            
            const baseStyle = aspectStyles[aspect.aspect_type] || {
                baseColor: 'rgba(148, 163, 184, 0.3)',
                baseWidth: 1.5,
                dasharray: 'none'
            };
            
            // Adjust style based on weight
            const style = {
                color: baseStyle.baseColor,
                width: baseStyle.baseWidth * weightMultiplier,
                dasharray: baseStyle.dasharray
            };
            
            // Skip very weak aspects if width is too small
            if (style.width < 0.4) return;

            // Special handling for Conjunctions
            if (aspect.aspect_type === 'Conjunction') {
                const pos1 = getCirclePosition(planet1.longitude, planetRadius);
                const pos2 = getCirclePosition(planet2.longitude, planetRadius);
                
                const dx = pos2.x - pos1.x;
                const dy = pos2.y - pos1.y;
                const distance = Math.sqrt(dx * dx + dy * dy);
                
                if (distance < 50) {
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
                    if (style.width > 2) {
                        path.setAttribute('filter', 'url(#conjunction-glow)');
                    }
                    
                    this.addAspectInteractions(path, aspect, style);
                    svg.appendChild(path);
                    
                } else {
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
                    if (style.width > 2) {
                        path.setAttribute('filter', 'url(#conjunction-glow)');
                    }
                    
                    this.addAspectInteractions(path, aspect, style);
                    svg.appendChild(path);
                }
                
                // Add endpoint markers for significant conjunctions
                if (style.width > 1) {
                    const marker1 = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
                    marker1.setAttribute('cx', pos1.x);
                    marker1.setAttribute('cy', pos1.y);
                    marker1.setAttribute('r', Math.min(4, style.width * 0.8));
                    marker1.setAttribute('fill', style.color);
                    marker1.setAttribute('class', 'conjunction-marker');
                    marker1.style.pointerEvents = 'none';

                    const marker2 = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
                    marker2.setAttribute('cx', pos2.x);
                    marker2.setAttribute('cy', pos2.y);
                    marker2.setAttribute('r', Math.min(4, style.width * 0.8));
                    marker2.setAttribute('fill', style.color);
                    marker2.setAttribute('class', 'conjunction-marker');
                    marker2.style.pointerEvents = 'none';

                    svg.appendChild(marker1);
                    svg.appendChild(marker2);
                }

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
            element.setAttribute('stroke-width', parseFloat(style.width) + 1.5);
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
            }

            svg.appendChild(group);
        });
    }

    drawAscendant(svg, center, ascendant, getCirclePosition) {
        const pos = getCirclePosition(ascendant.longitude, center - 30);
        const self = this;

        const group = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        group.style.cursor = 'pointer';

        const bgCircle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        bgCircle.setAttribute('cx', pos.x);
        bgCircle.setAttribute('cy', pos.y);
        bgCircle.setAttribute('r', '16');
        bgCircle.setAttribute('fill', 'rgba(30, 41, 59, 0.9)');
        bgCircle.setAttribute('stroke', 'rgba(168, 85, 247, 0.6)');
        bgCircle.setAttribute('stroke-width', '2');
        group.appendChild(bgCircle);

        const marker = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        marker.setAttribute('x', pos.x);
        marker.setAttribute('y', pos.y);
        marker.setAttribute('text-anchor', 'middle');
        marker.setAttribute('dominant-baseline', 'central');
        marker.setAttribute('fill', 'rgba(168, 85, 247, 1)');
        marker.setAttribute('font-size', '10');
        marker.setAttribute('font-weight', 'bold');
        marker.textContent = 'ASC';
        group.appendChild(marker);

        group.addEventListener('mouseenter', function (e) {
            bgCircle.setAttribute('fill', 'rgba(99, 102, 241, 0.4)');
            bgCircle.setAttribute('r', '18');
            marker.setAttribute('font-size', '12');
            self.showTooltip(e, 'angle', {
                name: 'Ascendant',
                symbol: 'ASC',
                sign: ascendant.sign,
                degree: ascendant.degree,
                description: 'Your rising sign - the mask you wear to the world'
            });
        });

        group.addEventListener('mousemove', function (e) {
            self.updateTooltipPosition(e);
        });

        group.addEventListener('mouseleave', function () {
            bgCircle.setAttribute('fill', 'rgba(30, 41, 59, 0.9)');
            bgCircle.setAttribute('r', '16');
            marker.setAttribute('font-size', '10');
            self.hideTooltip();
        });

        svg.appendChild(group);
    }

    drawMidheaven(svg, center, midheaven, getCirclePosition) {
        const pos = getCirclePosition(midheaven.longitude, center - 40);
        const self = this;

        const group = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        group.style.cursor = 'pointer';

        const marker = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        marker.setAttribute('x', pos.x);
        marker.setAttribute('y', pos.y);
        marker.setAttribute('text-anchor', 'middle');
        marker.setAttribute('dominant-baseline', 'central');
        marker.setAttribute('fill', 'rgba(168, 85, 247, 0.9)');
        marker.setAttribute('font-size', '12');
        marker.setAttribute('font-weight', 'bold');
        marker.textContent = 'MC';
        group.appendChild(marker);

        group.addEventListener('mouseenter', function (e) {
            marker.setAttribute('fill', 'rgba(168, 85, 247, 1)');
            marker.setAttribute('font-size', '14');
            self.showTooltip(e, 'angle', {
                name: 'Midheaven',
                symbol: 'MC',
                sign: midheaven.sign,
                degree: midheaven.degree,
                description: 'Your public image and career path'
            });
        });

        group.addEventListener('mousemove', function (e) {
            self.updateTooltipPosition(e);
        });

        group.addEventListener('mouseleave', function () {
            marker.setAttribute('fill', 'rgba(168, 85, 247, 0.9)');
            marker.setAttribute('font-size', '12');
            self.hideTooltip();
        });

        svg.appendChild(group);
    }

    showTooltip(event, type, data) {
        if (!this.tooltipElement) return;

        const icon = document.getElementById('tooltip-icon');
        const title = document.getElementById('tooltip-title');
        const content = document.getElementById('tooltip-content');

        if (type === 'planet') {
            icon.textContent = data.symbol;
            title.textContent = data.name;
            content.innerHTML = `
                <div><span class="tooltip-label">Sign:</span> <span class="tooltip-value">${data.sign} ${data.degree}°</span></div>
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
        } else if (type === 'angle') {
            icon.textContent = data.symbol;
            title.textContent = data.name;
            content.innerHTML = `
                <div><span class="tooltip-label">Sign:</span> <span class="tooltip-value">${data.sign} ${data.degree}°</span></div>
                <div class="tooltip-label" style="margin-top: 6px;">${data.description}</div>
            `;
        } else if (type === 'house') {
            icon.textContent = data.number.toString();
            title.textContent = `House ${data.number}`;
            const planetsText = data.planets.length > 0 
                ? data.planets.join(', ')
                : 'No planets';
            content.innerHTML = `
                <div><span class="tooltip-label">Sign:</span> <span class="tooltip-value">${data.sign} ${data.degree}°</span></div>
                <div><span class="tooltip-label">Planets:</span> <span class="tooltip-value">${planetsText}</span></div>
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
        const placeholderContainer = document.getElementById('planet-info-placeholder');
        const infoContent = document.getElementById('planet-info-content');

        if (!infoContainer || !infoContent) {
            console.warn('Planet info panel not found');
            return;
        }

        if (placeholderContainer) {
            placeholderContainer.classList.add('hidden');
        }
        infoContainer.classList.remove('hidden');

        if (typeof htmx !== 'undefined') {
            htmx.ajax('GET', `/deep_dives/planet/${planet.name}/`, {
                target: '#planet-info-content',
                swap: 'innerHTML'
            });
        } else {
            console.warn('HTMX not loaded');
        }
    }

    showAspectInfo(aspect) {
        const infoContainer = document.getElementById('planet-info');
        const placeholderContainer = document.getElementById('planet-info-placeholder');
        const infoContent = document.getElementById('planet-info-content');

        if (!infoContainer || !infoContent) {
            console.warn('Planet info panel not found');
            return;
        }

        if (placeholderContainer) {
            placeholderContainer.classList.add('hidden');
        }
        infoContainer.classList.remove('hidden');

        if (typeof htmx !== 'undefined') {
            htmx.ajax('GET', `/deep_dives/aspect/${aspect.planet1}/${aspect.planet2}/${aspect.aspect_type}/`, {
                target: '#planet-info-content',
                swap: 'innerHTML'
            });
        } else {
            console.warn('HTMX not loaded');
        }
    }
}

// Initialize global instance
window.chartRenderer = new ChartRenderer();