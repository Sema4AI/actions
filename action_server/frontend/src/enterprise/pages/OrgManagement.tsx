import { Box, Card, Header, List, Typography } from '@sema4ai/components';
import { IconUsers } from '@sema4ai/icons';

const OrgManagementPage = () => {
  return (
    <Box padding="$32" display="flex" flexDirection="column" gap="$24">
      <Header>
        <Header.Title title="Organization Management" icon={IconUsers} />
        <Header.Description>
          Placeholder UI for workspace configuration, member roles, and audit policies. Full CRUD
          flows connect in feature plan 004-backend-enterprise-features.
        </Header.Description>
      </Header>
      <Card bordered>
        <Typography variant="display.small">Capabilities roadmap</Typography>
        <List marginTop="$16" gap="$12">
          <List.Item>Role-based access control with predefined policy templates</List.Item>
          <List.Item>Workspace provisioning and lifecycle automation</List.Item>
          <List.Item>Audit log exports and retention policies</List.Item>
          <List.Item>Team-scoped OAuth and secret stores</List.Item>
        </List>
      </Card>
    </Box>
  );
};

export default OrgManagementPage;
