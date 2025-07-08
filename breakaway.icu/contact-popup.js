/**
 * 联系我们弹窗功能（无变灰遮罩，无换行，冒号对齐，点击外部关闭，无关闭按钮）
 * 1. 点击“联系我们”按钮，在按钮下方弹出联系弹窗，无任何变灰效果。
 * 2. 弹窗带有渐变动画。
 * 3. 点击弹窗外部区域可关闭弹窗，无关闭按钮。
 * 4. 代码自动插入弹窗DOM，无需手动写入HTML。
 * 5. 兼容移动端和PC端。
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
// 无遮罩层，无变灰效果，冒号对齐
(function injectContactPopupStyle() {
    if (document.getElementById('contact-popup-style')) return;
    const style = document.createElement('style');
    style.id = 'contact-popup-style';
    style.innerHTML = `
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
            <div class="contact-popup-value"><a href="mailto:breakaway@support.com" style="color:#2a4d8f;text-decoration:none;">breakaway@support.com</a></div>
        </div>
        <div class="contact-popup-row">
            <div class="contact-popup-label-wrap">
                <span class="contact-popup-label-text">微信公众号</span>
                <span class="contact-popup-colon">：</span>
            </div>
            <div class="contact-popup-value">XXXX</div>
        </div>
    </div>
`;

// 创建弹窗DOM（无遮罩层，无关闭按钮）
let popupEl;
let outsideClickHandler;
function createPopupDom() {
    if (popupEl) return;
    popupEl = createElement('div', { class: 'contact-popup-box' }, [
        (() => {
            const wrap = document.createElement('div');
            wrap.innerHTML = popupContent;
            return wrap;
        })()
    ]);
    document.body.appendChild(popupEl);

    // 外部点击关闭
    outsideClickHandler = function (e) {
        if (popupEl && !popupEl.contains(e.target)) {
            closePopup();
        }
    };
    setTimeout(() => { // 避免立即触发
        document.addEventListener('mousedown', outsideClickHandler, true);
        document.addEventListener('touchstart', outsideClickHandler, true);
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
    }

    // 激活动画
    setTimeout(() => {
        popupEl.classList.add('active');
    }, 10);

    // 禁止页面滚动
    document.body.style.overflow = 'hidden';
}

// 关闭弹窗
function closePopup() {
    if (!popupEl) return;
    popupEl.classList.remove('active');
    // 恢复页面滚动
    document.body.style.overflow = '';
    // 移除外部点击监听
    document.removeEventListener('mousedown', outsideClickHandler, true);
    document.removeEventListener('touchstart', outsideClickHandler, true);
    // 动画结束后移除DOM
    setTimeout(() => {
        if (popupEl && popupEl.parentNode) popupEl.parentNode.removeChild(popupEl);
        popupEl = null;
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
