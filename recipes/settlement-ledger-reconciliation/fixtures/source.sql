CREATE TABLE recipe_ledger (transaction_id text PRIMARY KEY, amount_cents bigint NOT NULL);
INSERT INTO recipe_ledger VALUES ('payment-1',1200),('refund-1',-200),('payment-2',450),('payment-4',100);
