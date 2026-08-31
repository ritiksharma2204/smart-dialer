import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  vus: 5,
  duration: '30s',
};

export default function () {
  const baseUrl = __ENV.BASE_URL;
  const campaignId = __ENV.CAMPAIGN_ID;

  const response = http.post(
    `${baseUrl}/campaigns/${campaignId}/dial`
  );

  check(response, {
    'status is 200': (r) => r.status === 200,
    'campaign id is correct': (r) => {
      try {
        return r.json('campaign_id') === Number(campaignId);
      } catch {
        return false;
      }
    },
  });

  sleep(1);
}
