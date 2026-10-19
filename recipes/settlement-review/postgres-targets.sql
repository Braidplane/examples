-- Run only in the dedicated local settlement_reporting database.
-- These deterministic upsert targets have no triggers or external side effects.
CREATE TABLE IF NOT EXISTS settlement_comparisons (
 evaluation_id text NOT NULL, batch_id text NOT NULL, line_id text NOT NULL,
 provider_event_id text NOT NULL, event_type text NOT NULL, order_id text NOT NULL,
 currency text NOT NULL, reported_gross bigint NOT NULL, reported_fee bigint NOT NULL,
 reported_net bigint NOT NULL, ledger_order_id text, ledger_gross bigint,
 difference numeric, unmatched bigint NOT NULL, PRIMARY KEY (evaluation_id, line_id)
);
CREATE TABLE IF NOT EXISTS settlement_totals (
 evaluation_id text NOT NULL, batch_id text NOT NULL, currency text NOT NULL,
 line_count bigint NOT NULL, matched_count bigint NOT NULL, unmatched_count numeric NOT NULL,
 reported_gross numeric NOT NULL, reported_fee numeric NOT NULL, reported_net numeric NOT NULL,
 matched_ledger_gross numeric, matched_difference numeric,
 PRIMARY KEY (evaluation_id, batch_id, currency)
);
