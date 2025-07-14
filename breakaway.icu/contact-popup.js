/**
 * 联系我们弹窗功能（有变灰遮罩，无换行，冒号对齐，点击外部关闭，无关闭按钮，带小三角气泡效果）
 * 1. 点击“联系我们”按钮，在按钮下方弹出联系弹窗，页面其他部分变灰，弹窗本身不变色。
 * 2. 弹窗带有渐变动画。
 * 3. 弹窗左上角有一个小三角，指向按钮，更像聊天气泡。
 * 4. 点击弹窗外部区域可关闭弹窗，无关闭按钮。
 * 5. 代码自动插入弹窗DOM，无需手动写入HTML。
 * 6. 兼容移动端和PC端。
 */

// 工具函数：创建DOM元素
function createElement(tag, attrs = {}, children = []) {
    const el = document.createElement(tag);
    for (const key in attrs) {
        if (key === "style") {
            Object.assign(el.style, attrs[key]);
        } else if (key.startsWith("on") && typeof attrs[key] === "function") {
            el.addEventListener(key.substring(2).toLowerCase(), attrs[key]);
        } else {
            el.setAttribute(key, attrs[key]);
        }
    }
    children.forEach(child => {
        if (typeof child === "string") {
            el.appendChild(document.createTextNode(child));
        } else if (child instanceof Node) {
            el.appendChild(child);
        }
    });
    return el;
}

// 弹窗样式（直接插入head，避免依赖css文件）
// 有遮罩层，冒号对齐，带三角气泡
(function injectContactPopupStyle() {
    if (document.getElementById('contact-popup-style')) return;
    const style = document.createElement('style');
    style.id = 'contact-popup-style';
    style.innerHTML = `
    .contact-popup-mask {
        position: fixed;
        z-index: 9999;
        left: 0; top: 0; right: 0; bottom: 0;
        width: 100vw;
        height: 100vh;
        background: rgba(44, 62, 80, 0.18);
        transition: opacity 0.28s cubic-bezier(.4,0,.2,1);
        opacity: 0;
        pointer-events: none;
    }
    .contact-popup-mask.active {
        opacity: 1;
        pointer-events: auto;
    }
    .contact-popup-box {
        position: fixed;
        z-index: 10000;
        min-width: 320px;
        max-width: 90vw;
        background: #fff;
        border-radius: 14px;
        box-shadow: 0 8px 32px rgba(42,77,143,0.13);
        padding: 28px 28px 18px 28px;
        opacity: 0;
        transform: translateY(20px) scale(0.98);
        transition: opacity 0.28s cubic-bezier(.4,0,.2,1), transform 0.28s cubic-bezier(.4,0,.2,1);
        pointer-events: none;
        filter: none !important;
        display: flex;
        flex-direction: column;
        align-items: flex-start;
    }
    .contact-popup-box.active {
        opacity: 1;
        transform: translateY(0) scale(1);
        pointer-events: auto;
    }
    .contact-popup-triangle {
        position: absolute;
        top: -12px;
        left: 32px;
        width: 0;
        height: 0;
        border-left: 12px solid transparent;
        border-right: 12px solid transparent;
        border-bottom: 12px solid #fff;
        z-index: 1;
        /* 阴影让三角更自然 */
        filter: drop-shadow(0 2px 4px rgba(42,77,143,0.10));
        pointer-events: none;
    }
    .contact-popup-content {
        font-size: 15px;
        color: #333;
        line-height: 1.7;
        margin-bottom: 8px;
        width: 100%;
        padding-top: 8px;
        box-sizing: border-box;
    }
    .contact-popup-row {
        display: flex;
        align-items: center;
        margin-bottom: 8px;
        white-space: nowrap;
        width: 100%;
    }
    .contact-popup-label-wrap {
        display: flex;
        align-items: center;
        min-width: 110px;
        flex-shrink: 0;
    }
    .contact-popup-label-text {
        color: #2a4d8f;
        font-weight: 500;
        font-size: 15px;
        text-align: left;
        white-space: nowrap;
        padding-right: 0;
    }
    .contact-popup-colon {
        display: inline-block;
        width: 18px;
        text-align: right;
        color: #2a4d8f;
        font-weight: 500;
        font-size: 15px;
        margin-right: 0;
        margin-left: 0;
        font-family: inherit;
    }
    .contact-popup-value {
        text-align: left;
        font-size: 15px;
        color: #333;
        flex: 1 1 auto;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        margin-left: 0;
    }
    @media (max-width: 600px) {
        .contact-popup-box {
            min-width: unset;
            padding: 18px 8px 14px 12px;
        }
        .contact-popup-label-wrap {
            min-width: 80px;
        }
        .contact-popup-label-text,
        .contact-popup-colon,
        .contact-popup-value {
            font-size: 14px;
        }
        .contact-popup-triangle {
            left: 20px;
        }
    }
    `;
    document.head.appendChild(style);
})();

// 弹窗内容（左对齐，冒号对齐，内容左对齐，不换行）
const popupContent = `
    <div class="contact-popup-content">
        <div class="contact-popup-row">
            <div class="contact-popup-label-wrap">
                <span class="contact-popup-label-text">邮箱</span>
                <span class="contact-popup-colon">：</span>
            </div>
            <div class="contact-popup-value"><a href="mailto:contact@breakaway.icu" style="color:#2a4d8f;text-decoration:none;">contact@breakaway.icu</a></div>
        </div>
        <div class="contact-popup-row">
            <div class="contact-popup-label-wrap">
                <span class="contact-popup-label-text">微信公众号</span>
                <span class="contact-popup-colon">：</span>
            </div>
            <div class="contact-popup-value"><span style="color:#2a4d8f;">超级兔子BFC</span></div>
        </div>
    </div>
`;

// 创建弹窗DOM（有遮罩层，无关闭按钮，带三角）
let popupEl;
let maskEl;
let outsideClickHandler;
function createPopupDom() {
    if (popupEl) return;
    // 遮罩层
    maskEl = createElement('div', { class: 'contact-popup-mask' });
    document.body.appendChild(maskEl);

    popupEl = createElement('div', { class: 'contact-popup-box', style: { position: 'fixed' } }, [
        // 小三角
        createElement('div', { class: 'contact-popup-triangle' }),
        (() => {
            const wrap = document.createElement('div');
            wrap.innerHTML = popupContent;
            return wrap;
        })()
    ]);
    document.body.appendChild(popupEl);

    // 外部点击关闭（点击遮罩层关闭）
    outsideClickHandler = function (e) {
        if (popupEl && maskEl && (e.target === maskEl)) {
            closePopup();
        }
    };
    setTimeout(() => { // 避免立即触发
        maskEl.addEventListener('mousedown', outsideClickHandler, true);
        maskEl.addEventListener('touchstart', outsideClickHandler, true);
    }, 20);
}

// 打开弹窗
function openPopup() {
    createPopupDom();

    // 定位弹窗到“联系我们”按钮下方
    const contactBtn = document.getElementById('contact-link');
    if (contactBtn) {
        const rect = contactBtn.getBoundingClientRect();
        let top = rect.bottom + window.scrollY + 8;
        let left = rect.left + window.scrollX;
        popupEl.style.visibility = 'hidden';
        popupEl.style.display = 'block';
        popupEl.classList.remove('active');
        // 先渲染到页面，获取宽高
        const popupRect = popupEl.getBoundingClientRect();

        // 计算三角的位置（让三角指向按钮左侧文字中心）
        // 三角的宽度是24px，left初始为32px
        // 让三角的中心对齐按钮的左侧文字
        // 先尝试获取按钮内文字的偏移
        let triangleLeft = 32; // 默认
        // 尝试更精确定位三角
        // 1. 获取按钮内文字的中心
        let btnTextCenter = rect.left + rect.width / 2;
        // 2. 弹窗左侧
        let popupLeft = left;
        // 3. 三角中心距离弹窗左侧的距离
        triangleLeft = Math.max(20, Math.min((btnTextCenter - popupLeft) - 12, popupRect.width - 44));
        // 设置三角位置
        const triangle = popupEl.querySelector('.contact-popup-triangle');
        if (triangle) {
            triangle.style.left = triangleLeft + 'px';
        }

        // 屏幕右侧溢出修正
        if (left + popupRect.width > window.innerWidth - 12) {
            left = window.innerWidth - popupRect.width - 12;
            if (left < 8) left = 8;
        }
        // 屏幕下方溢出修正
        if (top + popupRect.height > window.innerHeight - 12) {
            top = rect.top + window.scrollY - popupRect.height - 8;
            if (top < 8) top = 8;
        }
        popupEl.style.left = left + 'px';
        popupEl.style.top = top + 'px';
        popupEl.style.visibility = '';
        popupEl.style.display = '';

        // 再次修正三角位置（防止弹窗位置变化导致三角错位）
        setTimeout(() => {
            const popupRect2 = popupEl.getBoundingClientRect();
            let popupLeft2 = popupRect2.left;
            let btnTextCenter2 = rect.left + rect.width / 2;
            let triangleLeft2 = Math.max(20, Math.min((btnTextCenter2 - popupLeft2) - 12, popupRect2.width - 44));
            const triangle2 = popupEl.querySelector('.contact-popup-triangle');
            if (triangle2) {
                triangle2.style.left = triangleLeft2 + 'px';
            }
        }, 0);
    }

    // 激活动画
    setTimeout(() => {
        if (maskEl) maskEl.classList.add('active');
        popupEl.classList.add('active');
    }, 10);

    // 禁止页面滚动
    document.body.style.overflow = 'hidden';
}

// 关闭弹窗
function closePopup() {
    if (!popupEl) return;
    popupEl.classList.remove('active');
    if (maskEl) maskEl.classList.remove('active');
    // 恢复页面滚动
    document.body.style.overflow = '';
    // 移除外部点击监听
    if (maskEl) {
        maskEl.removeEventListener('mousedown', outsideClickHandler, true);
        maskEl.removeEventListener('touchstart', outsideClickHandler, true);
    }
    // 动画结束后移除DOM
    setTimeout(() => {
        if (popupEl && popupEl.parentNode) popupEl.parentNode.removeChild(popupEl);
        if (maskEl && maskEl.parentNode) maskEl.parentNode.removeChild(maskEl);
        popupEl = null;
        maskEl = null;
        outsideClickHandler = null;
    }, 300);
}

// 绑定“联系我们”按钮事件
window.addEventListener('DOMContentLoaded', function () {
    const contactBtn = document.getElementById('contact-link');
    if (contactBtn) {
        contactBtn.addEventListener('click', function (e) {
            e.preventDefault();
            if (!popupEl) openPopup();
        });
    }
});
