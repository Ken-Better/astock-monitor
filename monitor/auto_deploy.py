"""Copy dashboard to deploy folder for Netlify (GitHub Actions handles actual deploy)"""
import shutil
from .config import BASE_DIR, logger

def auto_deploy():
    """Copy dashboard.html from outputs to deploy/index.html for GitHub Actions deployment."""
    try:
        src = BASE_DIR / "outputs" / "dashboard.html"
        dst = BASE_DIR / "deploy" / "index.html"
        if src.exists():
            shutil.copy2(str(src), str(dst))
            logger.info("Deploy file synced: %s -> %s" % (src, dst))
            return True
        else:
            logger.warning("No dashboard to deploy (outputs/dashboard.html not found)")
            return False
    except Exception as e:
        logger.warning("Deploy sync error: %s" % e)
        return False
