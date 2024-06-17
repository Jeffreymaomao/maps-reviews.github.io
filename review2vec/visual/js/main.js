window.addEventListener("load", (e) => {
    const main = document.querySelector("main");
    const visualvector2 = new VisualVector2(main);
    window.visualvector2 = visualvector2;
});

class VisualVector2 {
    constructor(domParent) {
        // this.maxNum = 1000;
        this.maxNum = undefined;
        this.dom = {};
        this.dom.parent = domParent;
        this.style = {
            padding: 40,
            background: '#f0f0f0',
            point: {
                border: '0.1px',
                borderColor: '#ccc',
                colors: ['#E7ADAC', '#A2886D', '#A6BAAF', '#5B7493', '#4A475C'],
                // colors: ["#ff0000", "#00ff00", "#0000ff", "#ff00ff", "#00ffff"],
            }
        };

        fetch("./pca_clustered_reviews.json")
            .then(response => {
                return response.json();
            })
            .then(data => {
                this.data = this.preProcess(data);
                this.initDom();
                this.renderItems();
                this.addTooltipListener();
            })
            .catch(e => { console.error(e); })
    }
    preProcess(data) {
        data = data.slice(0, this.maxNum)
        const authors = data.map(item => item.author);
        const comments = data.map(item => item.comment);
        const stars = data.map(item => item.star);
        const clusters = data.map(item => item.cluster);
        const pca2_1 = data.map(item => item.pca2_1);
        const pca2_2 = data.map(item => item.pca2_2);
        const vectors = this.zip([pca2_1, pca2_2]);

        return {
            authors,
            stars,
            comments,
            clusters,
            vectors
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
        this.dom.container.style.background = this.style.background;
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
        this.data.vectors.forEach((vector, i) => {
            const x = xScale(vector[0]);
            const y = yScale(vector[1]);
            const cluster = this.data.clusters[i]
            const item = this.createAndAppendElement(container, 'div', {
                class: `point`,
                dataset: { index: i },
                style: `left: ${x}px; top: ${y}px; background-color: ${pointStyle.colors[cluster]}; border: ${pointStyle.border} solid ${pointStyle.borderColor}`
            });
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