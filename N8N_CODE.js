// n8n Code node, Run Once for Each Item, after video branch.
// If your node is Run Once for All Items, switch its mode first.
const item = $input.item.json;
if (!Array.isArray(item.scenes) || item.scenes.length !== 3) {
  throw new Error('Expected three scenes from Gemini');
}
const payload = {
  type: 'video',
  account: item.account,
  title: item.title,
  description: item.description,
  scenes: item.scenes
};
const payload_b64 = Buffer.from(JSON.stringify(payload), 'utf8').toString('base64');
if (payload_b64.length > 60000) throw new Error('GitHub input too large');
return { json: { ...item, payload_b64 } };
