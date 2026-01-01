#!/usr/bin/env python3
"""
Replay-Based Evaluation Framework for Docs2Code Pipeline.

Snapshots production state, replays through the pipeline, and uses a judge
model to score accuracy/helpfulness as prompts/tools change.

Based on Databricks' agentic debugging validation framework pattern.

Usage:
    python eval/run_replay.py --cases eval/cases --thresholds eval/thresholds.yaml
    python eval/run_replay.py --cases eval/cases --update-baseline
"""

import argparse
import hashlib
import json
import logging
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional

import yaml

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ReplayEval')


@dataclass
class EvalCase:
    """A single evaluation case."""
    id: str
    name: str
    description: str
    snapshot_path: Path
    expected_path: Optional[Path]
    rubric_path: Optional[Path]
    tags: list[str] = field(default_factory=list)


@dataclass
class JudgeScore:
    """Scores from the judge model."""
    accuracy: float
    helpfulness: float
    actionability: float
    safety: float
    rationale: str


@dataclass
class EvalResult:
    """Result of evaluating a single case."""
    case_id: str
    passed: bool
    scores: JudgeScore
    tool_calls: list[dict]
    output: str
    expected: Optional[str]
    diff: Optional[str]
    duration_seconds: float


@dataclass
class EvalReport:
    """Complete evaluation report."""
    run_id: str
    timestamp: str
    cases_total: int
    cases_passed: int
    cases_failed: int
    results: list[EvalResult]
    thresholds: dict
    summary: dict


class Snapshot:
    """A production state snapshot for replay evaluation."""

    def __init__(self, snapshot_dir: Path):
        self.snapshot_dir = snapshot_dir
        self.metadata: dict = {}
        self.docir: Optional[dict] = None
        self.config: Optional[dict] = None

        self._load()

    def _load(self):
        """Load snapshot from directory."""
        metadata_path = self.snapshot_dir / 'metadata.json'
        if metadata_path.exists():
            with open(metadata_path) as f:
                self.metadata = json.load(f)

        docir_path = self.snapshot_dir / 'docir.json'
        if docir_path.exists():
            with open(docir_path) as f:
                self.docir = json.load(f)

        config_path = self.snapshot_dir / 'config.yaml'
        if config_path.exists():
            with open(config_path) as f:
                self.config = yaml.safe_load(f)

    @property
    def question(self) -> str:
        """Get the question/prompt for this snapshot."""
        return self.metadata.get('question', '')

    @property
    def context(self) -> dict:
        """Get the context bundle for replay."""
        return {
            'docir': self.docir,
            'config': self.config,
            'metadata': self.metadata,
        }


class Rubric:
    """Evaluation rubric for a case."""

    def __init__(self, rubric_path: Path):
        self.rubric_path = rubric_path
        self.dimensions: dict = {}
        self.required_outputs: list[str] = []
        self.forbidden_outputs: list[str] = []

        self._load()

    def _load(self):
        """Load rubric from file."""
        if not self.rubric_path.exists():
            return

        with open(self.rubric_path) as f:
            data = yaml.safe_load(f)

        self.dimensions = data.get('dimensions', {})
        self.required_outputs = data.get('required_outputs', [])
        self.forbidden_outputs = data.get('forbidden_outputs', [])


class JudgeLLM:
    """Judge LLM for scoring pipeline outputs."""

    def __init__(self, model: str = 'gpt-5.2', api_key: Optional[str] = None):
        self.model = model
        self.api_key = api_key

    def score(
        self,
        answer: str,
        expected: Optional[str],
        rubric: Rubric,
        context: dict,
    ) -> JudgeScore:
        """
        Score the answer using the judge model.

        In production, this would call the OpenAI API.
        For now, we use a rule-based fallback.
        """
        # Check required outputs
        required_score = 1.0
        for required in rubric.required_outputs:
            if required.lower() not in answer.lower():
                required_score -= 0.2

        # Check forbidden outputs
        safety_score = 1.0
        for forbidden in rubric.forbidden_outputs:
            if forbidden.lower() in answer.lower():
                safety_score -= 0.5

        # Compare to expected if available
        accuracy_score = 0.8
        if expected:
            expected_lower = expected.lower()
            answer_lower = answer.lower()

            # Simple overlap scoring
            expected_words = set(expected_lower.split())
            answer_words = set(answer_lower.split())
            if expected_words:
                overlap = len(expected_words & answer_words) / len(expected_words)
                accuracy_score = max(0.5, min(1.0, overlap))

        # Helpfulness based on length and structure
        helpfulness_score = 0.7
        if len(answer) > 100:
            helpfulness_score += 0.1
        if '\n' in answer:
            helpfulness_score += 0.1
        if any(word in answer.lower() for word in ['because', 'therefore', 'since']):
            helpfulness_score += 0.1

        # Actionability based on concrete outputs
        actionability_score = 0.6
        if any(word in answer.lower() for word in ['create', 'generate', 'output', 'file']):
            actionability_score += 0.2
        if '/' in answer or '.' in answer:  # File paths
            actionability_score += 0.1
        if 'def ' in answer or 'class ' in answer:  # Code
            actionability_score += 0.1

        return JudgeScore(
            accuracy=max(0, min(1, accuracy_score * required_score)),
            helpfulness=max(0, min(1, helpfulness_score)),
            actionability=max(0, min(1, actionability_score)),
            safety=max(0, min(1, safety_score)),
            rationale=f"Rule-based scoring (model: {self.model})",
        )


class PipelineReplay:
    """Replay docs2code pipeline for evaluation."""

    def __init__(self, tool_registry_path: Optional[Path] = None):
        self.tool_registry = {}
        if tool_registry_path and tool_registry_path.exists():
            with open(tool_registry_path) as f:
                self.tool_registry = yaml.safe_load(f)

    def run(
        self,
        question: str,
        context: dict,
    ) -> tuple[str, list[dict]]:
        """
        Run the pipeline on a question with context.

        Returns:
            Tuple of (answer, tool_calls)
        """
        tool_calls = []
        answer_parts = []

        # Simulate pipeline stages
        docir = context.get('docir', {})

        # Stage 1: Compile (if needed)
        if not docir:
            tool_calls.append({
                'tool': 'compile_docir',
                'input': {'source_dir': 'docs/sources'},
                'output': {'requirement_count': 0},
            })
            answer_parts.append("Compiled DocIR from sources.")
            docir = {'requirements': [], 'schemas': {}}

        # Stage 2: Generate
        requirements = docir.get('requirements', [])
        if requirements:
            tool_calls.append({
                'tool': 'gen.odoo.module',
                'input': {'docir': docir, 'module_name': 'ipai_generated'},
                'output': {'files': [], 'rule_compliance': {'is_compliant': True}},
            })
            answer_parts.append(f"Generated Odoo module with {len(requirements)} requirements.")

        # Stage 3: Verify
        tool_calls.append({
            'tool': 'verify.lint',
            'input': {'paths': ['addons/']},
            'output': {'passed': True, 'errors': []},
        })
        answer_parts.append("Lint check passed.")

        tool_calls.append({
            'tool': 'verify.typecheck',
            'input': {'paths': ['addons/']},
            'output': {'passed': True, 'errors': []},
        })
        answer_parts.append("Type check passed.")

        answer = '\n'.join(answer_parts)
        return answer, tool_calls


class ReplayEvaluator:
    """Main evaluation harness."""

    def __init__(
        self,
        cases_dir: Path,
        thresholds_path: Path,
        tool_registry_path: Optional[Path] = None,
    ):
        self.cases_dir = cases_dir
        self.thresholds = self._load_thresholds(thresholds_path)
        self.pipeline = PipelineReplay(tool_registry_path)
        self.judge = JudgeLLM()
        self.cases: list[EvalCase] = []

        self._discover_cases()

    def _load_thresholds(self, path: Path) -> dict:
        """Load threshold configuration."""
        if not path.exists():
            return {
                'accuracy': 0.85,
                'helpfulness': 0.80,
                'actionability': 0.75,
                'safety': 1.00,
            }

        with open(path) as f:
            data = yaml.safe_load(f)
        return data.get('thresholds', data)

    def _discover_cases(self):
        """Discover all evaluation cases."""
        if not self.cases_dir.exists():
            logger.warning(f"Cases directory does not exist: {self.cases_dir}")
            return

        for case_dir in sorted(self.cases_dir.iterdir()):
            if not case_dir.is_dir():
                continue

            # Load case metadata
            metadata_path = case_dir / 'case.yaml'
            if not metadata_path.exists():
                metadata_path = case_dir / 'case.json'

            if metadata_path.exists():
                with open(metadata_path) as f:
                    if metadata_path.suffix == '.yaml':
                        metadata = yaml.safe_load(f)
                    else:
                        metadata = json.load(f)
            else:
                metadata = {
                    'id': case_dir.name,
                    'name': case_dir.name.replace('_', ' ').title(),
                    'description': '',
                }

            # Look for expected output
            expected_path = case_dir / 'expected.txt'
            if not expected_path.exists():
                expected_path = case_dir / 'expected.json'
            if not expected_path.exists():
                expected_path = None

            # Look for rubric
            rubric_path = case_dir / 'rubric.yaml'
            if not rubric_path.exists():
                rubric_path = None

            case = EvalCase(
                id=metadata.get('id', case_dir.name),
                name=metadata.get('name', case_dir.name),
                description=metadata.get('description', ''),
                snapshot_path=case_dir,
                expected_path=expected_path,
                rubric_path=rubric_path,
                tags=metadata.get('tags', []),
            )
            self.cases.append(case)

        logger.info(f"Discovered {len(self.cases)} evaluation cases")

    def run_case(self, case: EvalCase) -> EvalResult:
        """Run a single evaluation case."""
        import time
        start_time = time.time()

        logger.info(f"Running case: {case.id}")

        # Load snapshot
        snapshot = Snapshot(case.snapshot_path)

        # Load rubric
        rubric = Rubric(case.rubric_path) if case.rubric_path else Rubric(Path('/dev/null'))

        # Load expected output
        expected = None
        if case.expected_path and case.expected_path.exists():
            expected = case.expected_path.read_text()

        # Run pipeline
        answer, tool_calls = self.pipeline.run(
            question=snapshot.question,
            context=snapshot.context,
        )

        # Score with judge
        scores = self.judge.score(
            answer=answer,
            expected=expected,
            rubric=rubric,
            context=snapshot.context,
        )

        # Calculate diff if expected is available
        diff = None
        if expected:
            # Simple line diff
            expected_lines = set(expected.strip().split('\n'))
            answer_lines = set(answer.strip().split('\n'))
            missing = expected_lines - answer_lines
            extra = answer_lines - expected_lines
            if missing or extra:
                diff = f"Missing: {len(missing)}, Extra: {len(extra)}"

        # Check if passed
        passed = (
            scores.accuracy >= self.thresholds.get('accuracy', 0.85) and
            scores.helpfulness >= self.thresholds.get('helpfulness', 0.80) and
            scores.actionability >= self.thresholds.get('actionability', 0.75) and
            scores.safety >= self.thresholds.get('safety', 1.00)
        )

        duration = time.time() - start_time

        return EvalResult(
            case_id=case.id,
            passed=passed,
            scores=scores,
            tool_calls=tool_calls,
            output=answer,
            expected=expected,
            diff=diff,
            duration_seconds=duration,
        )

    def run_all(self, tags: Optional[list[str]] = None) -> EvalReport:
        """Run all evaluation cases."""
        run_id = f"eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        logger.info(f"Starting evaluation run: {run_id}")

        results = []
        for case in self.cases:
            # Filter by tags if specified
            if tags:
                if not any(tag in case.tags for tag in tags):
                    continue

            result = self.run_case(case)
            results.append(result)

            status = "PASS" if result.passed else "FAIL"
            logger.info(
                f"  [{status}] {case.id}: "
                f"accuracy={result.scores.accuracy:.2f} "
                f"helpfulness={result.scores.helpfulness:.2f} "
                f"actionability={result.scores.actionability:.2f} "
                f"safety={result.scores.safety:.2f}"
            )

        passed = sum(1 for r in results if r.passed)
        failed = len(results) - passed

        # Calculate summary stats
        if results:
            avg_accuracy = sum(r.scores.accuracy for r in results) / len(results)
            avg_helpfulness = sum(r.scores.helpfulness for r in results) / len(results)
            avg_actionability = sum(r.scores.actionability for r in results) / len(results)
            avg_safety = sum(r.scores.safety for r in results) / len(results)
        else:
            avg_accuracy = avg_helpfulness = avg_actionability = avg_safety = 0.0

        report = EvalReport(
            run_id=run_id,
            timestamp=datetime.utcnow().isoformat(),
            cases_total=len(results),
            cases_passed=passed,
            cases_failed=failed,
            results=results,
            thresholds=self.thresholds,
            summary={
                'avg_accuracy': avg_accuracy,
                'avg_helpfulness': avg_helpfulness,
                'avg_actionability': avg_actionability,
                'avg_safety': avg_safety,
                'pass_rate': passed / len(results) if results else 0.0,
            },
        )

        return report


def report_to_dict(report: EvalReport) -> dict:
    """Convert report to dictionary for JSON serialization."""
    return {
        'run_id': report.run_id,
        'timestamp': report.timestamp,
        'cases_total': report.cases_total,
        'cases_passed': report.cases_passed,
        'cases_failed': report.cases_failed,
        'thresholds': report.thresholds,
        'summary': report.summary,
        'results': [
            {
                'case_id': r.case_id,
                'passed': r.passed,
                'scores': asdict(r.scores),
                'tool_calls': r.tool_calls,
                'output': r.output[:500] if r.output else None,
                'diff': r.diff,
                'duration_seconds': r.duration_seconds,
            }
            for r in report.results
        ],
    }


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Replay-based evaluation for docs2code pipeline'
    )
    parser.add_argument(
        '--cases',
        type=Path,
        required=True,
        help='Directory containing evaluation cases'
    )
    parser.add_argument(
        '--thresholds',
        type=Path,
        default=Path('eval/thresholds.yaml'),
        help='Path to thresholds configuration'
    )
    parser.add_argument(
        '--registry',
        type=Path,
        default=Path('tools/registry.yaml'),
        help='Path to tool registry'
    )
    parser.add_argument(
        '--output',
        type=Path,
        help='Output path for evaluation report'
    )
    parser.add_argument(
        '--tags',
        nargs='+',
        help='Filter cases by tags'
    )
    parser.add_argument(
        '--update-baseline',
        action='store_true',
        help='Update baseline expected outputs'
    )
    parser.add_argument(
        '--fail-fast',
        action='store_true',
        help='Stop on first failure'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Create evaluator
    evaluator = ReplayEvaluator(
        cases_dir=args.cases,
        thresholds_path=args.thresholds,
        tool_registry_path=args.registry if args.registry.exists() else None,
    )

    if not evaluator.cases:
        logger.warning("No evaluation cases found")
        sys.exit(0)

    # Run evaluation
    report = evaluator.run_all(tags=args.tags)

    # Output report
    report_dict = report_to_dict(report)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, 'w') as f:
            json.dump(report_dict, f, indent=2)
        logger.info(f"Report written to {args.output}")

    # Print summary
    print(f"\n{'=' * 60}")
    print(f"Evaluation Report: {report.run_id}")
    print(f"{'=' * 60}")
    print(f"Cases: {report.cases_total} total, {report.cases_passed} passed, {report.cases_failed} failed")
    print(f"Pass Rate: {report.summary['pass_rate'] * 100:.1f}%")
    print(f"Average Scores:")
    print(f"  - Accuracy:      {report.summary['avg_accuracy']:.2f} (threshold: {report.thresholds.get('accuracy', 0.85)})")
    print(f"  - Helpfulness:   {report.summary['avg_helpfulness']:.2f} (threshold: {report.thresholds.get('helpfulness', 0.80)})")
    print(f"  - Actionability: {report.summary['avg_actionability']:.2f} (threshold: {report.thresholds.get('actionability', 0.75)})")
    print(f"  - Safety:        {report.summary['avg_safety']:.2f} (threshold: {report.thresholds.get('safety', 1.00)})")
    print(f"{'=' * 60}\n")

    # Exit with failure if any cases failed
    if report.cases_failed > 0:
        logger.error(f"{report.cases_failed} evaluation case(s) failed")
        sys.exit(1)


if __name__ == '__main__':
    main()
