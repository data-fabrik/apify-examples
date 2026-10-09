// One hotel, 7 consecutive nights, every booking site's offer, as a console table.
//
// Usage (Node 18+, `npm install apify-client`):
//   node hotel_rate_shopping.js "Ritz Paris" 2027-03-01 EUR
//
// The first argument is a hotel name, a Google Hotels link (contains /entity/...)
// or a Google id. With a name, check `matchedName`: it is the hotel Google picked.
// Cost: 7 nights x ($0.0025 per hotel with a price + $0.004 per hotel with offers)
// on the free plan, about $0.05. Nights without a price are free.
//
// Token: environment variable APIFY_TOKEN, nothing else.
'use strict';

const { ApifyClient } = require('apify-client'); // shortcut: CommonJS so the file runs without a package.json; switch to import if you add "type": "module"

const [hotel, checkIn, currency = 'USD'] = process.argv.slice(2);
if (!hotel || !checkIn) {
    console.error('usage: node hotel_rate_shopping.js "<hotel name or Google Hotels link>" <YYYY-MM-DD> [currency]');
    process.exit(1);
}
if (!process.env.APIFY_TOKEN) {
    console.error('APIFY_TOKEN is not set (Apify Console -> Settings -> API & Integrations)');
    process.exit(1);
}

const client = new ApifyClient({ token: process.env.APIFY_TOKEN });

(async () => {
    const run = await client.actor('datafabrik/google-hotels-scraper').call({
        locations: [],
        hotels: [hotel],
        checkIn,
        consecutiveDays: 7,
        nights: 1,
        currency,
        includeOffers: true,
    });
    const { items } = await client.dataset(run.defaultDatasetId).listItems();
    const rows = items.filter((i) => i.type === 'hotel');
    if (rows.length === 0) {
        const statuses = [...new Set(items.map((i) => i.status).filter(Boolean))];
        console.error(`no hotel row returned (status: ${statuses.join(', ') || 'unknown'}); nothing charged`);
        process.exit(2);
    }
    console.log(`${rows[0].matchedName || rows[0].name} (${currency})`);
    console.table(rows.map((h) => ({
        checkIn: h.checkIn,
        perNight: h.pricePerNight,
        perNightWithTaxes: h.pricePerNightWithTaxes,
        offers: h.offersCount ?? 0,
        cheapestSite: h.cheapestOffer?.provider ?? '',
        cheapestTotalWithTaxes: h.cheapestOffer?.totalPriceWithTaxes ?? '',
        officialSiteFirst: (h.offers || []).some((o) => o.isOfficialSite),
        deal: h.dealLabel || '',
    })));
})().catch((err) => {
    console.error(err.message);
    process.exit(1);
});
