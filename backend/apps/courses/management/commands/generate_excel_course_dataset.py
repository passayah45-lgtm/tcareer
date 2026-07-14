from __future__ import annotations

import csv
import random
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

DEFAULT_COLUMNS = [
    "order_id",
    "order_date",
    "region",
    "city",
    "salesperson",
    "product",
    "category",
    "units",
    "unit_price",
    "discount",
    "revenue",
    "cost",
    "profit",
    "customer_segment",
]


def generate_rows(*, rows: int, seed: int) -> list[dict[str, str]]:
    rng = random.Random(seed)  # noqa: S311 - deterministic synthetic dataset generation.
    regions = ["North", "south", " EAST ", "West", "west", "Central"]
    cities = ["Lagos", "Accra", " Nairobi ", "Kigali", "Dakar", "Abidjan"]
    products = [
        ("Laptop Stand", "Accessories", Decimal("24.50"), Decimal("13.25")),
        ("Wireless Mouse", "Accessories", Decimal("18.00"), Decimal("9.40")),
        ("Office Chair", "Furniture", Decimal("145.00"), Decimal("89.00")),
        ("Desk Lamp", "", Decimal("32.75"), Decimal("17.10")),
        ("Notebook Pack", "Stationery", Decimal("8.25"), Decimal("3.80")),
        ("USB-C Hub", "Electronics", Decimal("49.99"), Decimal("28.50")),
    ]
    segments = ["Consumer", "Small Business", "Enterprise", "Education"]
    salespeople = ["Salesperson A", "Salesperson B", "Salesperson C", "Salesperson D"]
    start = date(2026, 1, 1)
    output = []
    for index in range(rows):
        product, category, unit_price, unit_cost = rng.choice(products)
        units = rng.randint(1, 18)
        discount = rng.choice(
            [Decimal("0"), Decimal("0.05"), Decimal("0.10"), Decimal("0.15"), None]
        )
        order_date = start + timedelta(days=rng.randint(0, 180))
        if index % 17 == 0:
            date_text = order_date.strftime("%d/%m/%Y")
        elif index % 19 == 0:
            date_text = order_date.strftime("%m/%d/%Y")
        else:
            date_text = order_date.isoformat()
        discount_value = discount or Decimal("0")
        revenue = (unit_price * units * (Decimal("1") - discount_value)).quantize(Decimal("0.01"))
        cost = (unit_cost * units).quantize(Decimal("0.01"))
        profit = (revenue - cost).quantize(Decimal("0.01"))
        row = {
            "order_id": f"ORD-{1000 + index:04d}",
            "order_date": date_text,
            "region": rng.choice(regions),
            "city": rng.choice(cities),
            "salesperson": rng.choice(salespeople),
            "product": product if index % 23 else f" {product} ",
            "category": category,
            "units": str(units),
            "unit_price": str(unit_price),
            "discount": "" if discount is None else str(discount),
            "revenue": str(revenue),
            "cost": str(cost),
            "profit": str(profit),
            "customer_segment": rng.choice(segments),
        }
        output.append(row)
        if index in {28, 88}:
            duplicate = dict(row)
            output.append(duplicate)
    return output[:rows]


class Command(BaseCommand):
    help = "Generate the synthetic Excel for Data Analysis retail-sales dataset."

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            default="apps/courses/resources/excel_retail_sales_sample.csv",
        )
        parser.add_argument("--rows", type=int, default=150)
        parser.add_argument("--seed", type=int, default=20260714)
        parser.add_argument("--force", action="store_true")

    def handle(self, *args, **options):
        if options["rows"] < 150:
            raise CommandError("--rows must be at least 150 for the reviewed course dataset.")
        output_path = Path(options["output"])
        if not output_path.is_absolute():
            output_path = Path.cwd() / output_path
        if output_path.exists() and not options["force"]:
            raise CommandError(
                f"Refusing to overwrite existing dataset without --force: {output_path}"
            )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        rows = generate_rows(rows=options["rows"], seed=options["seed"])
        with output_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=DEFAULT_COLUMNS)
            writer.writeheader()
            writer.writerows(rows)
        self.stdout.write(self.style.SUCCESS(f"Generated {len(rows)} rows at {output_path}"))
