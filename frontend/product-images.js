const IMAGE_RULES = {
  Meat: {
    sausages: [
      "sausage", "sausages", "salami",
      "pepperoni", "chorizo", "bratwurst",
      "frankfurter", "hot dog", "kielbasa"
    ],

    poultry: [
      "chicken", "turkey", "duck",
      "goose", "poultry", "hen"
    ],

    pork: [
      "pork", "bacon", "ham",
      "prosciutto", "pancetta",
      "spareribs", "baby back ribs"
    ],

    beef: [
      "beef", "steak", "veal",
      "brisket", "ribeye", "sirloin",
      "angus", "wagyu", "filet mignon",
      "ground beef", "t-bone", "hamburger"
    ]
  },

  Seafood: {
    shellfish: [
      "shrimp", "prawn", "prawns",
      "mussel", "mussels",
      "clam", "clams",
      "oyster", "oysters",
      "scallop", "scallops",
      "lobster", "crab",
      "crayfish", "shellfish",
      "octopus", "squid", "calamari"
    ],

    fish: [
      "fish", "salmon", "tuna",
      "cod", "trout", "tilapia",
      "halibut", "mackerel",
      "sardine", "anchovy",
      "herring", "bass", "snapper"
    ]
  },

  Fruit: {
    apple: [
      "apple", "apples", "pear", "pears",
      "gala", "fuji", "honeycrisp", "granny smith"
    ],

    banan: [
      "banana", "bananas", "plantain", "plantains"
    ],

    berry: [
      "berry", "berries",
      "strawberry", "strawberries",
      "blueberry", "blueberries",
      "raspberry", "raspberries",
      "blackberry", "blackberries",
      "cranberry", "cranberries",
      "currant", "currants"
    ],

    Grape: [
      "grape", "grapes"
    ],

    "Mango-Ananas": [
      "mango", "mangos", "mangoes",
      "pineapple", "pineapples",
      "kiwi", "kiwifruit",
      "papaya", "papayas",
      "coconut", "coconuts",
      "passion fruit", "dragon fruit",
      "guava", "lychee", "pomegranate",
      "persimmon"
    ],

    orange: [
      "orange", "oranges",
      "lemon", "lemons",
      "lime", "limes",
      "grapefruit", "grapefruits",
      "mandarin", "mandarins",
      "clementine", "clementines",
      "tangerine", "tangerines",
      "pomelo", "citrus"
    ],

    melons: [
      "melon", "melons",
      "watermelon", "watermelons",
      "cantaloupe", "cantaloupes",
      "honeydew", "muskmelon",
      "galia"
    ],

    "stone-fruits": [
      "peach", "peaches",
      "plum", "plums",
      "apricot", "apricots",
      "nectarine", "nectarines",
      "cherry", "cherries",
      "pluot", "pluots"
    ]
  },
      Vegetables: {
      "tomatoes-peppers": [
      "tomato", "tomatoes",
      "pepper", "peppers",
      "bell pepper", "jalapeno", "jalapeño",
      "chili", "chilli", "poblano",
      "habanero", "serrano"
    ],

    "cucumbers-squash": [
      "cucumber", "cucumbers",
      "zucchini", "courgette",
      "squash", "pumpkin", "pumpkins",
      "eggplant", "eggplants",
      "aubergine", "butternut",
      "acorn squash"
    ],

    "root-vegetables": [
      "potato", "potatoes",
      "carrot", "carrots",
      "beet", "beets", "beetroot",
      "radish", "radishes",
      "turnip", "turnips",
      "parsnip", "parsnips",
      "yam", "yams",
      "ginger", "rutabaga", "daikon"
    ],

    "leafy-greens": [
      "lettuce", "spinach", "arugula",
      "salad", "greens", "kale",
      "romaine", "iceberg",
      "parsley", "cilantro", "basil",
      "dill", "mint", "chard",
      "celery", "asparagus", "watercress",
      "endive", "herbs"
    ],

    "cabbage-broccoli": [
      "cabbage", "cabbages",
      "broccoli", "cauliflower",
      "brussels sprouts", "bok choy",
      "broccolini", "kohlrabi",
      "romanesco"
    ],

    mushrooms: [
      "mushroom", "mushrooms",
      "shiitake", "portobello", "portabella",
      "cremini", "champignon",
      "porcini", "chanterelle", "enoki"
    ],

    "onions-garlic": [
      "onion", "onions",
      "garlic", "leek", "leeks",
      "shallot", "shallots",
      "scallion", "scallions",
      "chives"
    ],

    "peas-beans": [
      "pea", "peas",
      "bean", "beans",
      "corn", "sweetcorn",
      "edamame", "soybean", "soybeans",
      "lentil", "lentils",
      "chickpea", "chickpeas",
      "legumes", "okra"
    ]
  },
    Dairy: {
    "milk-yogurt": [
      "milk", "whole milk", "skim milk",
      "yogurt", "yoghurt",
      "kefir", "cream", "heavy cream",
      "sour cream", "buttermilk",
      "cream cheese"
    ],

    "cheese-butter": [
      "cheese", "cheddar", "mozzarella",
      "parmesan", "gouda", "swiss",
      "feta", "brie", "camembert",
      "ricotta", "cottage cheese",
      "butter"
    ]
  },
    Pantry: {
    sauces: [
      "sauce", "sauces",
      "ketchup", "mayonnaise", "mayo",
      "mustard", "sriracha", "tabasco",
      "bbq", "barbecue", "teriyaki",
      "pesto", "salsa", "dressing",
      "marinade", "aioli", "gravy"
    ],

    oils: [
      "oil", "oils",
      "olive oil", "sunflower oil",
      "vegetable oil", "canola oil",
      "coconut oil", "avocado oil",
      "sesame oil", "peanut oil",
      "corn oil", "grapeseed oil",
      "rapeseed oil", "cooking spray"
    ]
  },
      Pasta: {
    pasta: [
      "pasta", "spaghetti", "penne",
      "fusilli", "farfalle", "tagliatelle",
      "macaroni", "linguine", "fettuccine",
      "rigatoni", "lasagna", "lasagne",
      "ravioli", "tortellini", "noodle",
      "noodles", "orzo", "vermicelli",
      "gnocchi", "rotini", "bucatini",
      "angel hair", "ziti", "cannelloni",
      "pappardelle"
    ]
  }
};

const CATEGORY_IMAGES = {
  Meat: "meat/beef.png",
  Seafood: "seafood/fish.png",
  Fruit: "fruit/apple.png",
  Vegetables: "vegetables/leafy-greens.png",
  Dairy: "dairy/milk.png",
  Pantry: "pantry/sauces.png",
  Pasta: "pasta-grains/pasta.png"
};

function getProductImage(product) {
  const name = (product.name || "").toLowerCase();

  const category = (
    product.category || product.department || ""
  ).trim();

  const categories = category === "Meat & Seafood"
    ? ["Seafood", "Meat"]
    : [category];

  for (const currentCategory of categories) {
    const rules = IMAGE_RULES[currentCategory];

    if (!rules) continue;

    for (const [type, keywords] of Object.entries(rules)) {
      const matched = keywords.some(word => {
        const regex = new RegExp(`\\b${word}\\b`, "i");
        return regex.test(name);
      });

      if (matched) {
        return `/images/${currentCategory.toLowerCase()}/${type}.png`;
      }
    }
  }

  return CATEGORY_IMAGES[category]
    ? `/images/${CATEGORY_IMAGES[category]}`
    : null;
}