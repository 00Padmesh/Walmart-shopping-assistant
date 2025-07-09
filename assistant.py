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

        lowered = user_query.lower()

        # --- "I don't like this"
        if "i don't like this" in lowered or "i dont like this" in lowered:
            full_list = list(memory.full_product_lookup.values())
            current = memory.last_selected
            if current and full_list:
                try:
                    idx = full_list.index(current)
                    if idx + 1 < len(full_list):
                        next_product = full_list[idx + 1]
                        memory.last_selected = next_product
                        memory.last_products = [next_product]
                        reply = generate_reply(user_query, [next_product], "refine",
                                               intent=memory.intent, tone=memory.tone)
                        print(f"\n🤖 Assistant:\n{reply.strip()}\n")
                        print(format_product_card(next_product))
                    else:
                        print("⚠️ No more alternatives available. Try refining your search.")
                except ValueError:
                    print("⚠️ Couldn't locate previous selection in product list.")
            else:
                print("⚠️ No previous product to replace. Start with a product search.")
            continue

        # --- "I don't like any of these"
        if "i don't like any" in lowered or "i dont like any" in lowered:
            category = memory.get_category()
            filters = memory.get_filters()
            products = search_walmart_products(category, filters, max_results=10)
            if not products:
                print("⚠️ No better products found.")
                continue
            memory.save_products(products)
            reply = generate_reply(user_query, products[:3], "refine",
                                   intent=memory.intent, tone=memory.tone)
            print(f"\n🤖 Assistant:\n{reply.strip()}\n")
            for p in products[:3]:
                print(format_product_card(p))
            continue

        # Step 1: Build context for filter extraction
        full_context = f"Category: {memory.get_category()}\nFilters: {memory.get_filters()}\n"

        # Step 2: Extract structured filters and intent
        parsed = extract_filters(user_query, context=full_context)
        memory.update_context(parsed)

        action = parsed.get("action", "search")
        products = []

        # Step 3: Search if needed
        if action in ["search", "refine", "sort"]:
            category = memory.get_category()
            filters = memory.get_filters()
            products = search_walmart_products(category, filters, max_results=10)
            if not products:
                print("⚠️ No matching products found.")
                continue
            memory.save_products(products)

        # Step 4: Compare logic
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

        # Step 5: Reply
        reply = generate_reply(user_query, products[:3], action,
                               intent=memory.intent, tone=memory.tone)
        print(f"\n🤖 Assistant:\n{reply.strip()}\n")

        # Step 6: Display cards
        for p in products[:3]:
            print(format_product_card(p))

if __name__ == "__main__":
    run_assistant()
