# -*- coding: utf-8 -*-
import traceback

if __name__ == "__main__":
    try:
        from simapex.server import main
        main()
    except Exception:
        try:
            from simapex.server import scrivi_log
            scrivi_log(traceback.format_exc())
        except Exception:
            pass
