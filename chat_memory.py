class ChatMemory:
    def __init__(self):
        self.reset()

    def reset(self):
        self.category = None
        self.filters = {}  # brand, price_min, price_max, features
        self.sort_by = None
        self.last_action = None
        self.last_products = []  # list of dicts from SerpAPI
        self.last_selected = None  # product referred to as "this"
        self.product_lookup = {}  # title_lower → product
        self.last_sort_by = None

    def update_context(self, extraction_result):
        if extraction_result.get("category"):
            self.category = extraction_result["category"].lower()

        if extraction_result.get("brand") is not None:
            self.filters["brand"] = extraction_result["brand"]

        if extraction_result.get("price_min") is not None:
            self.filters["price_min"] = extraction_result["price_min"]

        if extraction_result.get("price_max") is not None:
            self.filters["price_max"] = extraction_result["price_max"]

        if extraction_result.get("features"):
            self.filters["features"] = extraction_result["features"]

        if extraction_result.get("sort_by"):
            self.sort_by = extraction_result["sort_by"]
            self.last_sort_by = extraction_result["sort_by"]

        self.last_action = extraction_result.get("action", "search")

    def save_products(self, products):
        self.last_products = products
        self.product_lookup = {p["title"].lower(): p for p in products if p.get("title")}
        if products:
            self.last_selected = products[0]

    def resolve_product_reference(self, name_or_ref):
        if not name_or_ref:
            return None

        name_or_ref = name_or_ref.lower()

        if name_or_ref in ["this", "that", "previous", "one"]:
            return self.last_selected

        for title, product in self.product_lookup.items():
            if name_or_ref in title:
                return product

        return None

    def get_category(self):
        return self.category

    def get_filters(self):
        return self.filters

    def get_sort_by(self):
        return self.sort_by

    def get_last_sort_by(self):
        return self.last_sort_by

    def get_last_action(self):
        return self.last_action

    def get_last_products(self):
        return self.last_products
