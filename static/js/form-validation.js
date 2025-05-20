// 表单验证脚本
document.addEventListener('DOMContentLoaded', function() {
    'use strict';
  
    // 获取所有需要验证的表单
    var forms = document.querySelectorAll('.needs-validation');
  
    // 循环处理每个表单并阻止提交
    Array.prototype.slice.call(forms).forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
                
                // 滚动到第一个无效字段
                const firstInvalidField = form.querySelector(':invalid');
                if (firstInvalidField) {
                    firstInvalidField.scrollIntoView({
                        behavior: 'smooth',
                        block: 'center'
                    });
                    firstInvalidField.focus();
                }
            } else {
                // 提交前显示加载状态
                const submitButton = form.querySelector('button[type="submit"]');
                if (submitButton) {
                    submitButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> 提交中...';
                    submitButton.disabled = true;
                }
            }
            
            form.classList.add('was-validated');
        }, false);
    });
    
    // 为所有文本输入添加去除首尾空格的功能
    const textInputs = document.querySelectorAll('input[type="text"], textarea');
    textInputs.forEach(input => {
        input.addEventListener('blur', function() {
            this.value = this.value.trim();
        });
    });
    
    // 处理MBTI单选框逻辑
    const mbtiRadios = document.querySelectorAll('[name="你的MBTI人格类型是什么？"]');
    const mbtiResultField = document.getElementById('mbti_result');
    
    if (mbtiRadios.length > 0 && mbtiResultField) {
        mbtiRadios.forEach(radio => {
            radio.addEventListener('change', function() {
                if (this.id === 'mbti_known') {
                    mbtiResultField.setAttribute('required', 'required');
                    mbtiResultField.focus();
                } else {
                    mbtiResultField.removeAttribute('required');
                }
            });
        });
        
        // 初始检查
        if (document.getElementById('mbti_known').checked) {
            mbtiResultField.setAttribute('required', 'required');
        }
    }
    
    // 处理多选框验证
    const checkboxesGroups = document.querySelectorAll('.form-check-input[type="checkbox"][name$="[]"]');
    const checkboxGroupNames = new Set();
    
    checkboxesGroups.forEach(checkbox => {
        const name = checkbox.getAttribute('name');
        checkboxGroupNames.add(name);
        
        checkbox.addEventListener('change', function() {
            validateCheckboxGroup(name);
        });
    });
    
    function validateCheckboxGroup(groupName) {
        const checkboxes = document.querySelectorAll(`input[name="${groupName}"]`);
        let isChecked = false;
        
        checkboxes.forEach(cb => {
            if (cb.checked) {
                isChecked = true;
            }
        });
        
        const firstCheckbox = checkboxes[0];
        if (firstCheckbox) {
            if (!isChecked) {
                firstCheckbox.setCustomValidity('请至少选择一项');
            } else {
                firstCheckbox.setCustomValidity('');
            }
        }
    }
    
    // 初始检查所有多选框组
    checkboxGroupNames.forEach(name => {
        validateCheckboxGroup(name);
    });
    
    // 实现字数统计功能（如果需要）
    const textareas = document.querySelectorAll('textarea[maxlength]');
    textareas.forEach(textarea => {
        const maxLength = textarea.getAttribute('maxlength');
        const counterDiv = document.createElement('div');
        counterDiv.className = 'form-text text-end';
        counterDiv.innerHTML = `<span class="current-count">0</span>/${maxLength}`;
        
        textarea.parentNode.insertBefore(counterDiv, textarea.nextSibling);
        
        textarea.addEventListener('input', function() {
            const currentLength = this.value.length;
            const counterSpan = counterDiv.querySelector('.current-count');
            counterSpan.textContent = currentLength;
            
            if (currentLength >= maxLength * 0.8) {
                counterSpan.classList.add('text-danger');
            } else {
                counterSpan.classList.remove('text-danger');
            }
        });
    });
    
    // 添加表单重置功能
    const resetButtons = document.querySelectorAll('button[type="reset"]');
    resetButtons.forEach(button => {
        button.addEventListener('click', function() {
            const form = this.closest('form');
            form.classList.remove('was-validated');
        });
    });
}); 