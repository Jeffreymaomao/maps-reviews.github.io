window.addEventListener("load", (e) => {
    const main = document.querySelector("main");
    const visualvector2 = new VisualVector2(main);
    window.visualvector2 = visualvector2;
});

/*
{
    "author":...
    "comment":...
    "star":5,
    "PCA":[-3.1391160488,0.0767028704],
    "cluster2":0,
    "cluster3":0,
    "cluster4":0,
    "cluster5":0,
    "anomaly-0.01":1,
    "anomaly-0.05":1,
    "anomaly-0.1":1,
    "anomaly-0.15":1,
    "anomaly-0.2":1}
*/

class VisualVector2 {
    constructor(domParent) {
        // this.maxNum = 1000;
        this.maxNum = undefined;
        this.dom = {};
        this.n_cluster = 2; // 2,3,4,5
        this.n_cmap = 0;
        this.n_background = 1;
        this.dom.parent = domParent;
        const _backgrounds = [250, 240, 100, 50, 20, 0];
        this.style = {
            padding: 40,
            backgrounds: _backgrounds.concat(_backgrounds.slice(1, -1).reverse()).map(v=>`rgb(${v},${v},${v})`),
            point: {
                border: '0.1px',
                borderColor: '#bbb'
            },
            cmaps: [
                ['#E7ADAC', '#A2886D', '#A6BAAF', '#5B7493', '#4A475C'],
                ["#ff0000", "#0ff000", "#000ff0", "#ff00ff", "#00ffff"],
                ['#FF6347', '#2E8B57', '#4682B4', '#708090', '#6A5ACD'],
                ['#20B2AA', '#778899', '#B0C4DE', '#BA55D3', '#9370DB'],
                ['#2E8B57', '#4682B4', '#708090', '#6A5ACD', '#FF6347'],
                ['#20B2AA', '#778899', '#B0C4DE', '#BA55D3', '#9370DB'],
                ['#8B0000', '#FF4500', '#32CD32', '#00CED1', '#1E90FF'],
                ['#FFD700', '#FF69B4', '#4B0082', '#8A2BE2', '#00FA9A'],
                ['#DC143C', '#00FF7F', '#FF8C00', '#8B008B', '#00BFFF']
            ] 
        };

        fetch("./pca_clustered_reviews-emojis.json")
            .then(response => {
                return response.json();
            })
            .then(data => {
                this.data = this.preProcess(data);
                this.initDom();
                this.renderItems();
                this.addTooltipListener();
                this.addKeyListener();
            })
            .catch(e => { console.error(e); })
    }
    preProcess(data) {
        data = data.slice(0, this.maxNum)
        const authors = data.map(item => item.author);
        const comments = data.map(item => item.comment);
        const stars = data.map(item => item.star);
        // const pca2_1 = data.map(item => item.pca2_1);
        // const pca2_2 = data.map(item => item.pca2_2);
        // const vectors = this.zip([pca2_1, pca2_2]);
        const vectors = data.map(item => item.PCA);
        
        const clusters2 = data.map(item => item.cluster2);
        const clusters3 = data.map(item => item.cluster3);
        const clusters4 = data.map(item => item.cluster4);
        const clusters5 = data.map(item => item.cluster5);

        
        return {
            authors,
            stars,
            comments,
            vectors,
            clusters2,
            clusters3,
            clusters4,
            clusters5,
        };
    }
    zip(arrays) {
        return arrays[0].map(function(_, i) {
            return arrays.map(function(array) { return array[i] })
        });
    }

    initDom() {
        this.dom.container = this.createAndAppendElement(this.dom.parent, "div", {
            id: 'container',
            style: 'height: 100%; width: 100%; position: relative;'
        });
        this.dom.tooltip = this.createAndAppendElement(this.dom.parent, "div", {
            id: 'tooltip',
        });
        this.dom.container.style.background = this.style.backgrounds[this.n_background];
    }

    renderItems() {
        const container = this.dom.container;

        container.innerHTML = ''; // 清空容器

        const width = container.clientWidth;
        const height = container.clientHeight;
        const padding = this.style.padding;
        const xRange = [Math.min(...this.data.vectors.map(v => v[0])), Math.max(...this.data.vectors.map(v => v[0]))];
        const yRange = [Math.min(...this.data.vectors.map(v => v[1])), Math.max(...this.data.vectors.map(v => v[1]))];

        const pad = this.style.padding;
        const xScale = (x) => (x - xRange[0]) / (xRange[1] - xRange[0]) * (width - 2 * pad) + pad;
        const yScale = (y) => (y - yRange[0]) / (yRange[1] - yRange[0]) * (height - 2 * pad) + pad;

        const pointStyle = this.style.point;
        this.dom.points = [];
        this.data.vectors.forEach((vector, i) => {
            const x = xScale(vector[0]);
            const y = yScale(vector[1]);
            const point = this.createAndAppendElement(container, 'div', {
                class: `point`,
                dataset: { index: i },
                style: `left: ${x}px; top: ${y}px; border: ${pointStyle.border} solid ${pointStyle.borderColor}`
            });
            this.dom.points.push(point);
        });
        this.renderItemsColor();
    }

    renderItemsColor(){
        const clusters = this.data[`clusters${this.n_cluster}`];
        this.dom.points.forEach((point, i) => {
            const cluster = clusters[i];
            point.style.backgroundColor = this.style.cmaps[this.n_cmap][cluster];
        });
    }

    addTooltipListener() {
        this.dom.container.addEventListener('mousemove', (e) => {
            const rect = this.dom.container.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            const elements = document.elementsFromPoint(e.clientX, e.clientY);
            const pointElement = elements.find(el => el.classList.contains('point'));

            if (pointElement) {
                const index = pointElement.dataset.index;
                const author = this.data.authors[index];
                const comment = this.data.comments[index].replace(/\n{1,}/g, '<br>');;
                const stars = this.data.stars[index];

                this.dom.tooltip.innerHTML = `
                    <div class="tooltip-author">${author}
                        <span class="tooltip-stars">${this.createStarsHTML(stars)}</span>
                    </div>
                    <div class="tooltip-comment">${comment}</div>
                `;

                const tooltipRect = this.dom.tooltip.getBoundingClientRect();
                let tooltipX = e.clientX + 10;
                let tooltipY = e.clientY + 10;

                if (tooltipX + tooltipRect.width > window.innerWidth) {
                    tooltipX = e.clientX - tooltipRect.width - 10;
                }

                if (tooltipY + tooltipRect.height > window.innerHeight) {
                    tooltipY = e.clientY - tooltipRect.height - 10;
                }

                if (tooltipX<0 || tooltipRect.width > window.innerWidth) {
                    tooltipX = window.innerWidth / 2 - tooltipRect.width / 2;
                }

                if (tooltipY<0 || tooltipRect.height > window.innerHeight) {
                    tooltipY = window.innerHeight / 2 - tooltipRect.height / 2;
                }

                this.dom.tooltip.style.left = `${tooltipX}px`;
                this.dom.tooltip.style.top = `${tooltipY}px`;
                this.dom.tooltip.style.display = 'block';
            } else {
                this.dom.tooltip.style.display = 'none';
            }
        });

        this.dom.container.addEventListener('mouseleave', () => {
            this.dom.tooltip.style.display = 'none';
        });
    }

    createStarsHTML(stars) {
        let starsHTML = '';
        for (let i = 0; i < stars; i++) {
            starsHTML += '★';
        }
        for (let i = stars; i < 5; i++) {
            starsHTML += '☆';
        }
        return starsHTML;
    }

    addKeyListener() {
        window.addEventListener('keydown', (e) => {
            if(e.code==='Digit2') {
                this.n_cluster = 2; this.renderItemsColor()
            } else if (e.code==='Digit3') {
                this.n_cluster = 3; this.renderItemsColor()
            } else if (e.code==='Digit4') {
                this.n_cluster = 4; this.renderItemsColor()
            } else if (e.code==='Digit5') {
                this.n_cluster = 5; this.renderItemsColor()
            } else if (e.code==='KeyC') {
                this.n_cmap += 1;
                this.n_cmap = (this.n_cmap)%(this.style.cmaps.length);
                this.renderItemsColor()
            } else if  (e.code==='KeyB') {
                this.n_background += 1;
                this.n_background = (this.n_background)%(this.style.backgrounds.length);
                this.dom.container.style.background = this.style.backgrounds[this.n_background];
            }
        });
    }

    createAndAppendElement(parent, tag, attributes = {}) {
        const element = document.createElement(tag);

        // class 
        if (attributes.class) {
            attributes.class.split(" ").forEach(className => element.classList.add(className));
            delete attributes.class; // delete class in attributes
        }
        // dataset
        if (attributes.dataset) {
            Object.keys(attributes.dataset).forEach(key => element.dataset[key] = attributes.dataset[key]);
            delete attributes.dataset; // delete dataset in attributes
        }
        // other attributes
        Object.keys(attributes).forEach(key => element[key] = attributes[key]);

        if (parent) parent.appendChild(element);
        return element;
    }

}