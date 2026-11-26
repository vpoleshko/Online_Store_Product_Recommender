import pandas as pd

from src.recommender.recipes import RecipeIndex


def make_index():
    recipes = pd.DataFrame(
        {
            "recipe_id": [1, 2],
            "name": ["tomato pasta", "omelette"],
            "minutes": [20, 10],
            "n_steps": [3, 2],
            "n_reviews": [10, 5],
            "rating": [4.5, 4.2],
        }
    )
    recipe_ingredients = pd.DataFrame(
        {
            "recipe_id": [1, 1, 1, 1, 2, 2, 2],
            "ingredient": ["pasta", "tomato", "basil", "salt", "egg", "cheese", "salt"],
            "is_staple": [False, False, False, True, False, False, True],
        }
    )
    links = pd.DataFrame(
        {
            "ingredient": ["pasta", "tomato", "tomato", "basil", "egg", "cheese"],
            "product_id": [10, 20, 21, 30, 40, 50],
            "is_primary": [True, True, False, True, True, True],
        }
    )
    return RecipeIndex(recipes, recipe_ingredients, links)


def test_match_finds_recipe_covered_by_cart():
    index = make_index()

    matches = index.match([10, 20])

    assert [index.recipes.at[row, "name"] for row, *_ in matches] == ["tomato pasta"]
    _, have, total, _ = matches[0]
    assert (have, total) == (2, 3)


def test_any_linked_product_covers_an_ingredient():
    index = make_index()

    assert index.match([10, 21])[0][1] == 2


def test_missing_products_are_primary_products_of_uncovered_ingredients():
    index = make_index()

    assert index.missing_products(0, [10, 20]) == [("basil", 30)]


def test_candidates_suggest_products_that_complete_recipes():
    index = make_index()

    found = index.candidates([10, 20])

    assert set(found) == {30}
    best_score, n_recipes, share, row = found[30]
    assert n_recipes == 1 and round(share, 2) == 0.67 and index.recipes.at[row, "name"] == "tomato pasta"


def test_unrelated_cart_matches_nothing():
    assert make_index().match([999]) == []
