'''from semantic_search import semantic_search
from filter_extraction import extract_filters
from reply_generator import generate_natural_reply
from chat_memory import ChatMemory
from fuzzywuzzy import fuzz
import pandas as pd


class Assistant:
    def __init__(self, df):
        self.df = df
        self.memory = ChatMemory()
        self.last_filtered_df = pd.DataFrame()
        self.last_query = ""

    def handle_query(self, query):
        print(f"🧩 Received query: {query}")
        context = self.memory.get_context()
        print(f"📚 Current context: {context if context else 'None'}")

        extracted = extract_filters(query, context)
        print(f"🧪 Extracted filters: {extracted}")
        self.memory.update_context(query)

        if not extracted:
            return "⚠️ Sorry, I couldn't understand your request."

        action = extracted.get("action", "search")

        if action == "compare":
            return self._compare_products_llm(query, extracted)
        elif action in ["search", "recommend"]:
            return self._search_and_respond(query, extracted)
        else:
            return "🤖 I'm not sure what you'd like me to do. Can you rephrase?"

    def _search_and_respond(self, query, filters):
        print(f"📥 Calling semantic search with: {query}")
        result_df = semantic_search(query)
        if result_df.empty:
            return "⚠️ Sorry, I couldn't find any matching products."

        print(f"🔢 Result count: {len(result_df)}")
        filtered_df = self._apply_filters(result_df, filters)
        print(f"🔎 Filtered results count: {len(filtered_df)}")

        self.last_filtered_df = filtered_df
        self.last_query = query

        return generate_natural_reply(query, self.memory.get_context(), filtered_df)

    def _apply_filters(self, df, filters):
        if filters.get("brand"):
            brands = [b.lower() for b in filters["brand"]]
            df = df[df["title"].str.lower().str.contains("|".join(brands))]

        if filters.get("features"):
            features = [f.lower() for f in filters["features"]]
            df = df[df["title"].str.lower().str.contains("|".join(features))]

        if filters.get("price_min") is not None:
            df = df[df["price"] >= filters["price_min"]]

        if filters.get("price_max") is not None:
            df = df[df["price"] <= filters["price_max"]]

        if filters.get("sort_by") == "price_asc":
            df = df.sort_values("price", ascending=True)
        elif filters.get("sort_by") == "price_desc":
            df = df.sort_values("price", descending=False)
        elif filters.get("sort_by") == "rating":
            df = df.sort_values("stars", ascending=False)

        return df

    def _compare_products_llm(self, query, filters):
        if self.last_filtered_df.empty:
            return "⚠️ I need some product results to compare first. Try searching again."

        mentions = filters.get("products", [])
        print(f"📝 Mentions to compare: {mentions}")
        resolved = self._resolve_product_mentions(mentions)

        if len(resolved) < 2:
            return "⚠️ One or both products could not be found for comparison."

        df = pd.DataFrame(resolved)
        return generate_natural_reply(query, self.memory.get_context(), df)

    def _resolve_product_mentions(self, mentions):
        resolved = []
        seen_titles = set()

        for mention in mentions:
            best_score = 0
            best_match = None

            for _, row in self.last_filtered_df.iterrows():
                title = row["title"]
                score = fuzz.token_sort_ratio(mention.lower(), title.lower())
                print(f"🧠 Fuzzy match '{mention}' vs '{title[:40]}...' = {score}")

                if score > best_score and title not in seen_titles:
                    best_score = score
                    best_match = row

            if best_score >= 50:
                resolved.append(best_match)
                seen_titles.add(best_match["title"])
                print(f"✅ Matched '{mention}' → '{best_match['title'][:40]}...' (score: {best_score})")
            else:
                fallback_df = semantic_search(mention)
                if not fallback_df.empty:
                    match = fallback_df.iloc[0]
                    resolved.append(match)
                    seen_titles.add(match["title"])
                    print(f"🆘 Semantic fallback matched '{mention}' → '{match['title'][:40]}...'")
                else:
                    print(f"❌ No good match found for '{mention}'")

        return resolved'''


from filter_extraction import extract_filters
from walmart_search import search_walmart_products
from chat_memory import ChatMemory
from reply_generator import generate_reply

def format_product_card(p):
    return f"""
🛍️ {p['title']}
💲 {p['price']}    ⭐ {p.get('rating', 'N/A')} stars
🔗 {p['url']}
"""

def run_assistant():
    memory = ChatMemory()

    print("🛒 Welcome to your Walmart Shopping Assistant!")
    print("Type your query, or 'exit' to quit.\n")

    while True:
        user_query = input("👤 You: ").strip()
        if user_query.lower() in ["exit", "quit"]:
            print("👋 Goodbye!")
            break

        # Step 1: Build context for filter extraction
        full_context = f"Category: {memory.get_category()}\nFilters: {memory.get_filters()}\n"

        # Step 2: Extract structured filters and intent
        parsed = extract_filters(user_query, context=full_context)
        new_category = parsed.get("category")
        old_category = memory.get_category()

        memory.update_context(parsed)
        action = parsed.get("action", "search")
        products = []

        if action in ["search", "refine", "sort"]:
            # Determine if we need to fetch again
            if action == "search" or (new_category and new_category.lower() != old_category):
                query = new_category or user_query
                filters = memory.get_filters()
                products = search_walmart_products(query, filters, max_results=10)
                memory.save_products(products)
            else:
                # Use previous results
                products = memory.get_last_products()

        elif action == "compare":
            refs = parsed.get("products", [])
            if len(refs) < 2:
                print("⚠️ Please mention two products to compare.")
                continue

            ref1 = memory.resolve_product_reference(refs[0])
            ref2 = memory.resolve_product_reference(refs[1])

            if ref1 and ref2:
                products = [ref1, ref2]
            else:
                print("⚠️ Couldn’t find one or both products to compare.")
                continue

        if not products:
            print("⚠️ No matching products found.")
            continue

        # Step 3: Generate natural reply
        reply = generate_reply(user_query, products, action)
        print(f"\n🤖 Assistant:\n{reply.strip()}\n")

        # Step 4: Display product cards
        for p in products:
            print(format_product_card(p))

if __name__ == "__main__":
    run_assistant()
