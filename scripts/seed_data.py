#!/usr/bin/env python3
"""
Sake Sensei - Data Seeding Script

Loads master data from JSON files and seeds DynamoDB tables.
"""

import json
import sys
from decimal import Decimal
from pathlib import Path
from typing import Any

import boto3
from botocore.exceptions import ClientError

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.models.brewery import Brewery
from backend.models.sake import Sake


def load_json_file(file_path: Path) -> list[dict[str, Any]]:
    """Load and parse JSON file.

    Args:
        file_path: Path to JSON file

    Returns:
        List of dictionaries from JSON

    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If JSON is invalid
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    with file_path.open() as f:
        data: list[dict[str, Any]] = json.load(f)
        return data


def convert_to_dynamodb_types(obj: Any) -> Any:
    """Convert Python types to DynamoDB-compatible types.

    Args:
        obj: Object to convert

    Returns:
        DynamoDB-compatible object
    """
    # Import pydantic URL types
    try:
        from pydantic_core import Url as PydanticUrl
    except ImportError:
        PydanticUrl = None

    if isinstance(obj, float):
        return Decimal(str(obj))
    elif PydanticUrl and isinstance(obj, PydanticUrl):
        return str(obj)
    elif isinstance(obj, dict):
        return {k: convert_to_dynamodb_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_dynamodb_types(v) for v in obj]
    elif hasattr(obj, '__class__') and 'pydantic' in obj.__class__.__module__:
        # Catch any other pydantic types
        return str(obj)
    else:
        return obj


def seed_breweries(dynamodb: Any, table_name: str, breweries_data: list[dict[str, Any]]) -> int:
    """Seed brewery master data into DynamoDB.

    Args:
        dynamodb: boto3 DynamoDB resource
        table_name: Name of brewery table
        breweries_data: List of brewery data dictionaries

    Returns:
        Number of breweries successfully inserted
    """
    table = dynamodb.Table(table_name)
    success_count = 0

    for brewery_dict in breweries_data:
        try:
            # Validate with Pydantic model
            brewery = Brewery(**brewery_dict)

            # Convert to dict for DynamoDB (with ISO datetime strings)
            item = brewery.model_dump()
            item["created_at"] = brewery.created_at.isoformat()
            item["updated_at"] = brewery.updated_at.isoformat()

            # Convert website URL to string
            if "website" in item and item["website"] is not None:
                item["website"] = str(item["website"])

            # Convert float to Decimal for DynamoDB
            item = convert_to_dynamodb_types(item)

            # Insert into DynamoDB
            table.put_item(Item=item)

            print(f"✅ Inserted brewery: {brewery.name} ({brewery.brewery_id})")
            success_count += 1

        except ClientError as e:
            print(f"❌ DynamoDB error inserting {brewery_dict.get('brewery_id', 'unknown')}: {e}")
        except Exception as e:
            print(f"❌ Error processing {brewery_dict.get('brewery_id', 'unknown')}: {e}")

    return success_count


def seed_sake(dynamodb: Any, table_name: str, sake_data: list[dict[str, Any]]) -> int:
    """Seed sake master data into DynamoDB.

    Args:
        dynamodb: boto3 DynamoDB resource
        table_name: Name of sake table
        sake_data: List of sake data dictionaries

    Returns:
        Number of sake successfully inserted
    """
    table = dynamodb.Table(table_name)
    success_count = 0

    for sake_dict in sake_data:
        try:
            # Validate with Pydantic model
            sake = Sake(**sake_dict)

            # Convert to dict for DynamoDB (with ISO datetime strings)
            item = sake.model_dump()
            item["created_at"] = sake.created_at.isoformat()
            item["updated_at"] = sake.updated_at.isoformat()

            # Convert float to Decimal for DynamoDB
            item = convert_to_dynamodb_types(item)

            # Insert into DynamoDB
            table.put_item(Item=item)

            print(f"✅ Inserted sake: {sake.name} ({sake.sake_id})")
            success_count += 1

        except ClientError as e:
            print(f"❌ DynamoDB error inserting {sake_dict.get('sake_id', 'unknown')}: {e}")
        except Exception as e:
            print(f"❌ Error processing {sake_dict.get('sake_id', 'unknown')}: {e}")

    return success_count


def main() -> None:
    """Main seeding function."""
    print("🌱 Sake Sensei - Data Seeding Script")
    print("=" * 60)

    # Get project root directory
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data"

    # File paths
    brewery_file = data_dir / "brewery_master.json"
    sake_file = data_dir / "sake_master.json"

    # DynamoDB table names (can be overridden with env vars)
    import os

    brewery_table_name = os.getenv("BREWERY_TABLE_NAME", "SakeSensei-BreweryMaster")
    sake_table_name = os.getenv("SAKE_TABLE_NAME", "SakeSensei-SakeMaster")

    try:
        # Load data files
        print("\n📂 Loading data files...")
        breweries_data = load_json_file(brewery_file)
        print(f"   Loaded {len(breweries_data)} breweries from {brewery_file.name}")

        sake_data = load_json_file(sake_file)
        print(f"   Loaded {len(sake_data)} sake from {sake_file.name}")

        # Initialize DynamoDB client
        print("\n🔌 Connecting to DynamoDB...")
        dynamodb = boto3.resource("dynamodb", region_name=os.getenv("AWS_REGION", "us-west-2"))

        # Seed breweries first (sake reference brewery_id)
        print(f"\n🏭 Seeding breweries into {brewery_table_name}...")
        brewery_count = seed_breweries(dynamodb, brewery_table_name, breweries_data)

        # Seed sake
        print(f"\n🍶 Seeding sake into {sake_table_name}...")
        sake_count = seed_sake(dynamodb, sake_table_name, sake_data)

        # Summary
        print("\n" + "=" * 60)
        print("✅ Seeding completed successfully!")
        print(f"   Breweries inserted: {brewery_count}/{len(breweries_data)}")
        print(f"   Sake inserted: {sake_count}/{len(sake_data)}")

        if brewery_count < len(breweries_data) or sake_count < len(sake_data):
            print("\n⚠️  Some items failed to insert. Check error messages above for details.")
            sys.exit(1)

    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"\n❌ JSON parsing error: {e}")
        sys.exit(1)
    except ClientError as e:
        print(f"\n❌ AWS/DynamoDB error: {e}")
        print("\nMake sure:")
        print("  1. AWS credentials are configured")
        print("  2. DynamoDB tables exist")
        print("  3. You have permissions to write to the tables")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
