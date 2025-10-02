import os
import sys
import json


def setup_django():
    ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    PROJECT_PKG = os.path.join(ROOT, 'bankprocessor')
    if ROOT not in sys.path:
        sys.path.insert(0, ROOT)
    if PROJECT_PKG not in sys.path:
        sys.path.insert(0, PROJECT_PKG)
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bankprocessor.settings')
    import django
    django.setup()


def main():
    try:
        setup_django()
        from django.test import RequestFactory
        # imports aquí después de django.setup()
        from processor import views  # type: ignore[import]
        from processor.models import ProcessingJob  # type: ignore[import]

        job = ProcessingJob.objects.order_by('-started_at').first()
        print('latest job id:', getattr(job, 'id', None))
        if not job:
            print('no jobs found')
            return

        rf = RequestFactory()
        req = rf.get(f'/api/results/?job_id={job.id}')
        resp = views.processing_results_json(req)
        print('status:', resp.status_code)
        try:
            payload = json.loads(resp.content.decode('utf-8'))
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        except Exception:
            print(resp.content.decode('utf-8'))

    except Exception as exc:
        print('Error en check_results_api:', exc)


if __name__ == '__main__':
    main()
