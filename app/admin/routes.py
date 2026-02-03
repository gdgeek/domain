"""Admin routes for web interface."""
import json
from functools import wraps
from flask import render_template, request, redirect, url_for, flash, session, current_app
from app.admin import admin_bp
from app.services import domain_service, config_service, ValidationError, NotFoundError, DuplicateError


def require_password(f):
    """Decorator to require password authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        admin_password = current_app.config.get('ADMIN_PASSWORD')
        # No password configured = no auth required
        if not admin_password:
            return f(*args, **kwargs)
        # Check if already authenticated
        if session.get('admin_authenticated'):
            return f(*args, **kwargs)
        # Redirect to login
        return redirect(url_for('admin.login', next=request.url))
    return decorated_function


@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Admin login page."""
    admin_password = current_app.config.get('ADMIN_PASSWORD')
    if not admin_password:
        return redirect(url_for('admin.index'))
    
    if request.method == 'POST':
        password = request.form.get('password', '')
        if password == admin_password:
            session['admin_authenticated'] = True
            next_url = request.args.get('next') or url_for('admin.index')
            return redirect(next_url)
        flash('密码错误', 'error')
    
    return render_template('login.html')


@admin_bp.route('/logout')
def logout():
    """Admin logout."""
    session.pop('admin_authenticated', None)
    flash('已退出登录', 'success')
    return redirect(url_for('admin.login'))


@admin_bp.route('/')
@require_password
def index():
    """Admin index - redirect to domain list."""
    return redirect(url_for('admin.domain_list'))


@admin_bp.route('/domains')
@require_password
def domain_list():
    """List all domains."""
    domains = domain_service.list_domains()
    return render_template('domains/list.html', domains=domains)


@admin_bp.route('/domains/new', methods=['GET', 'POST'])
@require_password
def domain_create():
    """Create new domain."""
    if request.method == 'POST':
        try:
            domain = domain_service.create_domain(
                name=request.form.get('name'),
                description=request.form.get('description'),
                is_active=request.form.get('is_active') == 'on'
            )
            flash(f"域名 '{domain.name}' 创建成功", 'success')
            return redirect(url_for('admin.domain_list'))
        except (ValidationError, DuplicateError) as e:
            flash(str(e), 'error')
    
    return render_template('domains/form.html', domain=None)


@admin_bp.route('/domains/<int:id>/edit', methods=['GET', 'POST'])
@require_password
def domain_edit(id):
    """Edit domain."""
    try:
        domain = domain_service.get_domain(id)
    except NotFoundError as e:
        flash(str(e), 'error')
        return redirect(url_for('admin.domain_list'))
    
    if request.method == 'POST':
        try:
            domain = domain_service.update_domain(
                domain_id=id,
                name=request.form.get('name'),
                description=request.form.get('description'),
                is_active=request.form.get('is_active') == 'on'
            )
            flash(f"域名 '{domain.name}' 更新成功", 'success')
            return redirect(url_for('admin.domain_list'))
        except (ValidationError, DuplicateError) as e:
            flash(str(e), 'error')
    
    return render_template('domains/form.html', domain=domain)


@admin_bp.route('/domains/<int:id>/delete', methods=['POST'])
@require_password
def domain_delete(id):
    """Delete domain."""
    try:
        domain = domain_service.get_domain(id)
        domain_name = domain.name
        domain_service.delete_domain(id)
        flash(f"域名 '{domain_name}' 已删除", 'success')
    except NotFoundError as e:
        flash(str(e), 'error')
    
    return redirect(url_for('admin.domain_list'))


@admin_bp.route('/domains/<int:domain_id>/configs')
@require_password
def config_list(domain_id):
    """List configs for a domain."""
    try:
        domain = domain_service.get_domain(domain_id)
        configs = config_service.list_configs_by_domain(domain_id)
        supported_languages = current_app.config.get('SUPPORTED_LANGUAGES', [])
        existing_languages = [c.language for c in configs]
        available_languages = [l for l in supported_languages if l not in existing_languages]
        
        return render_template('configs/list.html', 
                               domain=domain, 
                               configs=configs,
                               available_languages=available_languages)
    except NotFoundError as e:
        flash(str(e), 'error')
        return redirect(url_for('admin.domain_list'))


@admin_bp.route('/domains/<int:domain_id>/configs/new', methods=['GET', 'POST'])
@require_password
def config_create(domain_id):
    """Create new config for domain."""
    try:
        domain = domain_service.get_domain(domain_id)
    except NotFoundError as e:
        flash(str(e), 'error')
        return redirect(url_for('admin.domain_list'))
    
    if request.method == 'POST':
        try:
            data_str = request.form.get('data', '{}')
            data = json.loads(data_str) if data_str else {}
            
            config = config_service.create_config(
                domain_id=domain_id,
                language=request.form.get('language', 'zh-CN'),
                data=data
            )
            flash(f"配置 ({config.language}) 创建成功", 'success')
            return redirect(url_for('admin.config_list', domain_id=domain_id))
        except json.JSONDecodeError:
            flash("配置数据必须是有效的 JSON 格式", 'error')
        except (ValidationError, DuplicateError) as e:
            flash(str(e), 'error')
    
    supported_languages = current_app.config.get('SUPPORTED_LANGUAGES', [])
    existing_configs = config_service.list_configs_by_domain(domain_id)
    existing_languages = [c.language for c in existing_configs]
    available_languages = [l for l in supported_languages if l not in existing_languages]
    
    return render_template('configs/form.html', 
                           domain=domain, 
                           config=None,
                           available_languages=available_languages)


@admin_bp.route('/domains/<int:domain_id>/configs/<string:language>/edit', methods=['GET', 'POST'])
@require_password
def config_edit(domain_id, language):
    """Edit config."""
    try:
        domain = domain_service.get_domain(domain_id)
        config = config_service.get_config(domain_id, language)
    except NotFoundError as e:
        flash(str(e), 'error')
        return redirect(url_for('admin.domain_list'))
    
    if request.method == 'POST':
        try:
            data_str = request.form.get('data', '{}')
            data = json.loads(data_str) if data_str else {}
            
            config = config_service.update_config(
                domain_id=domain_id,
                language=language,
                data=data
            )
            flash(f"配置 ({config.language}) 更新成功", 'success')
            return redirect(url_for('admin.config_list', domain_id=domain_id))
        except json.JSONDecodeError:
            flash("配置数据必须是有效的 JSON 格式", 'error')
        except (ValidationError, NotFoundError) as e:
            flash(str(e), 'error')
    
    return render_template('configs/form.html', 
                           domain=domain, 
                           config=config,
                           available_languages=[])


@admin_bp.route('/domains/<int:domain_id>/configs/<string:language>/delete', methods=['POST'])
@require_password
def config_delete(domain_id, language):
    """Delete config."""
    try:
        config_service.delete_config(domain_id, language)
        flash(f"配置 ({language}) 已删除", 'success')
    except NotFoundError as e:
        flash(str(e), 'error')
    
    return redirect(url_for('admin.config_list', domain_id=domain_id))
