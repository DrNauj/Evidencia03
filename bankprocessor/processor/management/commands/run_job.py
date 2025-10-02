from django.core.management.base import BaseCommand, CommandError
from processor.models import ProcessingJob

class Command(BaseCommand):
    help = 'Run a ProcessingJob by id in a separate process (invokes processor.ml_processor.process_bank_data)'

    def add_arguments(self, parser):
        parser.add_argument('job_id', type=int)

    def handle(self, *args, **options):
        job_id = options['job_id']
        job = ProcessingJob.objects.filter(id=job_id).first()
        if not job:
            raise CommandError(f'No job with id {job_id}')

        # Import here to avoid Django setup issues when this file is parsed
        from processor.ml_processor import process_bank_data
        import os, logging

        # localizar data_path consistente con views
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
        data_path = os.path.join(project_root, 'data', 'bank.csv')
        data_path = os.path.abspath(data_path)

        # configurar logging a fichero para este run
        logs_dir = os.path.join(project_root, 'job_logs')
        os.makedirs(logs_dir, exist_ok=True)
        logfile = os.path.join(logs_dir, f'run_job_{job.id}.log')
        logging.basicConfig(filename=logfile, level=logging.INFO)

        logging.info(f"Starting process_bank_data for job {job.id} with data_path={data_path}")

        try:
            process_bank_data(data_path, job)
            logging.info(f"process_bank_data finished for job {job.id} - status={job.status}")
        except Exception as e:
            # process_bank_data should update job.status, but ensure fallback
            from django.utils import timezone
            job.status = 'error'
            job.error_message = str(e)
            job.completed_at = timezone.now()
            job.save()
            logging.exception(f"Exception running job {job.id}: {e}")
            raise
