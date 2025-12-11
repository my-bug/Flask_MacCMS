// 后台管理JavaScript功能

// 自定义确认对话框
function showCustomConfirm(message, onConfirm, onCancel) {
    // 创建遮罩层
    const overlay = document.createElement('div');
    overlay.className = 'confirm-overlay';
    
    // 创建对话框
    const dialog = document.createElement('div');
    dialog.className = 'confirm-dialog';
    
    // 对话框内容
    dialog.innerHTML = `
        <div class="confirm-header">提示</div>
        <div class="confirm-body">${message.replace(/\n/g, '<br>')}</div>
        <div class="confirm-footer">
            <button class="confirm-btn confirm-cancel">取消</button>
            <button class="confirm-btn confirm-ok">确定</button>
        </div>
    `;
    
    overlay.appendChild(dialog);
    document.body.appendChild(overlay);
    
    // 显示动画
    setTimeout(() => {
        overlay.classList.add('show');
    }, 10);
    
    // 关闭对话框
    function closeDialog() {
        overlay.classList.remove('show');
        setTimeout(() => {
            document.body.removeChild(overlay);
        }, 300);
    }
    
    // 绑定按钮事件
    const cancelBtn = dialog.querySelector('.confirm-cancel');
    const okBtn = dialog.querySelector('.confirm-ok');
    
    cancelBtn.addEventListener('click', () => {
        closeDialog();
        if (onCancel) onCancel();
    });
    
    okBtn.addEventListener('click', () => {
        closeDialog();
        if (onConfirm) onConfirm();
    });
    
    // 点击遮罩层关闭
    overlay.addEventListener('click', (e) => {
        if (e.target === overlay) {
            closeDialog();
            if (onCancel) onCancel();
        }
    });
}

document.addEventListener('DOMContentLoaded', function() {
    // 自动隐藏闪现消息
    const flashContainer = document.querySelector('.flash-messages-container');
    if (flashContainer) {
        setTimeout(() => {
            flashContainer.style.transition = 'opacity 0.5s';
            flashContainer.style.opacity = '0';
            setTimeout(() => flashContainer.remove(), 500);
        }, 5000);
    }
    
    // 表单验证
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const requiredInputs = form.querySelectorAll('[required]');
            let isValid = true;
            
            requiredInputs.forEach(input => {
                if (!input.value.trim()) {
                    isValid = false;
                    input.style.borderColor = 'red';
                } else {
                    input.style.borderColor = '#ddd';
                }
            });
            
            if (!isValid) {
                e.preventDefault();
                alert('请填写所有必填字段');
            }
        });
    });
    
    // 为所有带有data-confirm属性的表单添加确认对话框
    const confirmForms = document.querySelectorAll('form[data-confirm]');
    confirmForms.forEach(form => {
        // 检查是否已经添加过事件监听
        if (!form.dataset.confirmHandled) {
            form.dataset.confirmHandled = 'true';
            form.addEventListener('submit', function(e) {
                e.preventDefault();
                const message = form.getAttribute('data-confirm');
                
                showCustomConfirm(message, () => {
                    // 确认后提交表单
                    form.removeAttribute('data-confirm');
                    form.submit();
                });
            });
        }
    });

    // 为所有带有data-confirm属性的按钮添加确认对话框
    const confirmButtons = document.querySelectorAll('button[data-confirm]:not(form[data-confirm] button)');
    confirmButtons.forEach(button => {
        if (!button.dataset.confirmHandled) {
            button.dataset.confirmHandled = 'true';
            button.addEventListener('click', function(e) {
                e.preventDefault();
                const message = button.getAttribute('data-confirm');
                
                showCustomConfirm(message, () => {
                    // 确认后触发按钮的原始行为
                    button.removeAttribute('data-confirm');
                    button.click();
                });
            });
        }
    });
    
    // 表格行高亮
    const tableRows = document.querySelectorAll('.data-table tbody tr');
    tableRows.forEach(row => {
        row.addEventListener('click', function(e) {
            if (e.target.tagName !== 'BUTTON' && e.target.tagName !== 'A') {
                tableRows.forEach(r => r.style.backgroundColor = '');
                this.style.backgroundColor = '#e3f2fd';
            }
        });
    });
    
    // 搜索框实时提示
    const searchInput = document.querySelector('.search-form input');
    if (searchInput) {
        let searchTimeout;
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            const value = this.value.trim();
            
            if (value.length > 0) {
                this.style.borderColor = '#2c3e50';
            } else {
                this.style.borderColor = '#ddd';
            }
        });
    }
    
    // 图片URL预览
    const imageInputs = document.querySelectorAll('input[name="vod_pic"]');
    imageInputs.forEach(input => {
        input.addEventListener('blur', function() {
            const url = this.value.trim();
            if (url && (url.startsWith('http://') || url.startsWith('https://'))) {
                // 可以添加图片预览功能
                console.log('图片URL:', url);
            }
        });
    });
    
    // 数字输入验证
    const numberInputs = document.querySelectorAll('input[type="number"]');
    numberInputs.forEach(input => {
        input.addEventListener('input', function() {
            if (this.value < 0) {
                this.value = 0;
            }
        });
    });
    
    // 文本域自动调整高度
    const textareas = document.querySelectorAll('textarea');
    textareas.forEach(textarea => {
        textarea.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
        });
    });
});

// 工具函数：格式化日期
function formatDate(timestamp) {
    const date = new Date(timestamp * 1000);
    return date.toLocaleString('zh-CN');
}

// 工具函数：复制到剪贴板
function copyToClipboard(text) {
    const textarea = document.createElement('textarea');
    textarea.value = text;
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand('copy');
    document.body.removeChild(textarea);
    alert('已复制到剪贴板');
}
