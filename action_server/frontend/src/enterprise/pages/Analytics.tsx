import { Box, Card, Grid, Header, Typography } from '@sema4ai/components';
import { IconChartAnalytics } from '@sema4ai/icons';

const chartPlaceholders = [
  { title: 'Run Health', description: 'Track success rate across action packages.' },
  { title: 'Execution Time', description: 'Identify slow actions and performance regressions.' },
  { title: 'Failure Categories', description: 'Group failures by root cause and severity.' },
];

const AnalyticsPage = () => {
  return (
    <Box padding="$32" display="flex" flexDirection="column" gap="$24">
      <Header>
        <Header.Title title="Analytics" icon={IconChartAnalytics} />
        <Header.Description>
          Enterprise dashboards for operational insight. Visualizations are placeholders until the
          backend data pipeline lands in feature plan 004-backend-enterprise-features.
        </Header.Description>
      </Header>
      <Grid columns={{ base: 1, m: 2, l: 3 }} gap="$24">
        {chartPlaceholders.map((item) => (
          <Card key={item.title} bordered>
            <Typography variant="display.small">{item.title}</Typography>
            <Typography marginTop="$12" variant="body.default" color="neutral">
              {item.description}
            </Typography>
            <Box
              marginTop="$24"
              height="200px"
              background="surface.muted"
              borderRadius="$12"
              borderColor="border.default"
              borderWidth="$1"
            />
          </Card>
        ))}
      </Grid>
    </Box>
  );
};

export default AnalyticsPage;
