from filter_extraction import extract_filters
from walmart_search import search_walmart_products
from chat_memory import ChatMemory
from reply_generator import generate_reply
from recommender import recommend_best_product

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
            print("👋 Goodbye! Come back anytime.")
            break

        lowered = user_query.lower()

        # --- Help command
        if lowered in ["help", "what can you do", "commands"]:
            print("""
ℹ️ I can help you with:
- Searching for products
- Sorting and filtering
- Comparing two items
- Recommending the best item
- Tracking what you like/dislike
- Refining results when you're unhappy

Try things like:
→ "Show me wireless gaming mice under 1000"
→ "Which one is best?"
→ "Compare Logitech and Razer"
→ "I don't like this"
""")
            continue

        # --- Recommendation: "Which one is best?"
        if any(phrase in lowered for phrase in [
            "which one is best", "which is best", "what do you recommend",
            "recommend one", "suggest one", "your top pick"
        ]):
            full_list = list(memory.full_product_lookup.values())
            if not full_list:
                print("⚠️ No products to recommend. Try searching first.")
                continue

            best = recommend_best_product(memory, full_list)
            if best:
                memory.last_selected = best
                memory.last_products = [best]
                reply = generate_reply(user_query, [best], "refine",
                                       intent=memory.intent, tone=memory.tone)
                print(f"\n🤖 Assistant:\n{reply.strip()}\n")
                print(format_product_card(best))
            else:
                print("⚠️ Couldn't find a recommendation right now.")
            continue

        # --- Like command
        if "i like this" in lowered:
            current = memory.last_selected
            if current:
                memory.like_product(current)
                print("👍 Got it! I'll remember you liked this one.")
            else:
                print("⚠️ No product currently selected to like.")
            continue

        # --- Dislike current item
        if "i don't like this" in lowered or "i dont like this" in lowered:
            full_list = list(memory.full_product_lookup.values())
            current = memory.last_selected
            if current and full_list:
                try:
                    idx = full_list.index(current)
                    memory.dislike_product(current)
                    if idx + 1 < len(full_list):
                        next_product = full_list[idx + 1]
                        memory.last_selected = next_product
                        memory.last_products = [next_product]
                        reply = generate_reply(user_query, [next_product], "refine",
                                               intent=memory.intent, tone=memory.tone)
                        print(f"\n🤖 Assistant:\n{reply.strip()}\n")
                        print(format_product_card(next_product))
                    else:
                        print("😕 That was the last one I had. Try searching again!")
                except ValueError:
                    print("⚠️ Hmm, couldn't locate that product in my list.")
            else:
                print("⚠️ You haven’t selected any product yet. Start with a search.")
            continue

        # --- Dislike all
        if "i don't like any" in lowered or "i dont like any" in lowered:
            category = memory.get_category()
            filters = memory.get_filters()
            if not category:
                print("⚠️ I need a category first. Try saying what you're shopping for.")
                continue

            products = search_walmart_products(category, filters, max_results=10)
            if not products:
                print("😕 I couldn’t find anything better. Maybe tweak the filters?")
                continue

            memory.save_products(products)
            reply = generate_reply(user_query, products[:3], "refine",
                                   intent=memory.intent, tone=memory.tone)
            print(f"\n🤖 Assistant:\n{reply.strip()}\n")
            for p in products[:3]:
                print(format_product_card(p))
            continue

        # --- Step 1: Build context for extraction
        full_context = f"Category: {memory.get_category()}\nFilters: {memory.get_filters()}\n"

        # --- Step 2: Extract filters, intent, tone, etc.
        parsed = extract_filters(user_query, context=full_context)
        memory.update_context(parsed)

        action = parsed.get("action", "search")
        products = []

        # --- Step 3: Handle search / refine / sort
        if action in ["search", "refine", "sort"]:
            category = memory.get_category()
            filters = memory.get_filters()
            if not category:
                print("⚠️ Please mention what you're looking for.")
                continue

            products = search_walmart_products(category, filters, max_results=10)
            if not products:
                print("😕 I couldn’t find matching products. Try adjusting your request.")
                continue

            memory.save_products(products)

        # --- Step 4: Handle comparison
        elif action == "compare":
            refs = parsed.get("products", [])
            if len(refs) < 2:
                print("⚠️ Please name two products you'd like to compare.")
                continue

            ref1 = memory.resolve_product_reference(refs[0])
            ref2 = memory.resolve_product_reference(refs[1])

            if ref1 and ref2:
                products = [ref1, ref2]
            else:
                print("⚠️ Couldn’t find one or both items to compare.")
                continue

        # --- Fallback
        if not products:
            print("⚠️ No products to show yet. Try searching first.")
            continue

        # --- Step 5: Generate and print response
        reply = generate_reply(user_query, products[:3], action,
                               intent=memory.intent, tone=memory.tone)
        print(f"\n🤖 Assistant:\n{reply.strip()}\n")

        # --- Step 6: Show product cards
        for p in products[:3]:
            print(format_product_card(p))

if __name__ == "__main__":
    run_assistant()
