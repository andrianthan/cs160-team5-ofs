// Placeholder picture for a Product with no imageUrl: a category-colored tile with an emoji.
const CATEGORY_STYLES: Record<string, { emoji: string; bg: string }> = {
    Produce: { emoji: "🥬", bg: "bg-brand-100" },
    Dairy: { emoji: "🥛", bg: "bg-sky-100" },
    Bakery: { emoji: "🍞", bg: "bg-gold-100" },
    Pantry: { emoji: "🫒", bg: "bg-lime-100" },
};
const FALLBACK = { emoji: "🛒", bg: "bg-brand-50" };

// A better emoji from the product name when we recognise it; the tile color still follows the category.
const NAME_EMOJI: [RegExp, string][] = [
    [/apple/i, "🍎"], [/potato/i, "🥔"], [/spinach|kale|lettuce|greens/i, "🥬"],
    [/carrot/i, "🥕"], [/tomato/i, "🍅"], [/banana/i, "🍌"], [/egg/i, "🥚"], [/milk/i, "🥛"],
    [/cheese/i, "🧀"], [/butter/i, "🧈"], [/sourdough|bread|loaf/i, "🍞"], [/oat/i, "🌾"], [/olive/i, "🫒"],
];

export default function CategoryThumb({
    category,
    name,
    className = "aspect-square w-full rounded-2xl text-6xl",
}: {
    category?: string;
    name?: string;
    className?: string;
}) {
    const base = (category && CATEGORY_STYLES[category]) || FALLBACK;
    const emoji = (name && NAME_EMOJI.find(([re]) => re.test(name))?.[1]) || base.emoji;
    const bg = base.bg;
    return (
        <div aria-hidden="true" className={`flex items-center justify-center ${bg} ${className}`}>
            {emoji}
        </div>
    );
}
