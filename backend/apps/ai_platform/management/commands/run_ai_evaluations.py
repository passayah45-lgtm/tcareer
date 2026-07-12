from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from apps.ai_platform.services import AIEvaluationOpsService


class Command(BaseCommand):
    help = "Run scheduled-ready AI evaluation datasets with optional filters."

    def add_arguments(self, parser):
        parser.add_argument("--dataset-type", default="", help="Filter by AI evaluation dataset type.")
        parser.add_argument("--feature", default="", help="Filter by AI feature.")
        parser.add_argument("--provider", default="", help="Provider type to run against.")
        parser.add_argument("--prompt-version", default="", help="Prompt version label to attach to runs.")
        parser.add_argument("--limit", type=int, default=50, help="Maximum datasets to run.")
        parser.add_argument("--dry-run", action="store_true", help="List matching datasets without executing.")
        parser.add_argument("--actor-email", default="", help="Optional platform admin actor email for audit attribution.")

    def handle(self, *args, **options):
        actor = None
        if options["actor_email"]:
            actor = get_user_model().objects.filter(email=options["actor_email"]).first()
        result = AIEvaluationOpsService.run_scheduled(
            actor=actor,
            dataset_type=options["dataset_type"],
            feature=options["feature"],
            provider_type=options["provider"],
            prompt_version=options["prompt_version"],
            limit=options["limit"],
            dry_run=options["dry_run"],
        )
        if result["dry_run"]:
            self.stdout.write(f"Dry run matched {result['dataset_count']} dataset(s):")
            for dataset in result["datasets"]:
                self.stdout.write(f"- {dataset}")
            return
        self.stdout.write(self.style.SUCCESS(f"Executed {len(result['runs'])} AI evaluation run(s)."))
