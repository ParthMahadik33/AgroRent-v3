from flask import Blueprint, render_template
from utils.auth import login_required

bp = Blueprint('dashboard', __name__)

@bp.route('/rentdashboard')
@login_required
def rentdashboard():
    """Renting dashboard page"""
    return render_template('rentdashboard.html')

@bp.route('/listdashboard')
@login_required
def listdashboard():
    """Listing dashboard page"""
    return render_template('listdashboard.html')

@bp.route('/renting')
@login_required
def renting():
    """Renting page with equipment listings"""
    return render_template('renting.html')

@bp.route('/heatmap')
def heatmap():
    """Heatmap visualization page"""
    return render_template('heatmap.html')
