UPDATE share_links SET expires_at = now() - interval '1 minute' WHERE link_id = 'SHL-0008';
