import { Box, Card, Form, Header, Input, Stack, Switch, Typography } from '@sema4ai/components';
import { IconLock } from '@sema4ai/icons';

const SsoPage = () => {
  return (
    <Box padding="$32" display="flex" flexDirection="column" gap="$24">
      <Header>
        <Header.Title title="Single Sign-On" icon={IconLock} />
        <Header.Description>
          Configure SAML or OIDC providers for centralized identity. This is scaffolding only—form
          submission hooks arrive with feature plan 004-backend-enterprise-features.
        </Header.Description>
      </Header>
      <Card bordered>
        <Form>
          <Stack gap="$24">
            <Form.Field>
              <Form.Label htmlFor="provider">Identity Provider Name</Form.Label>
              <Input id="provider" placeholder="e.g. Okta, Azure AD" />
            </Form.Field>
            <Form.Field>
              <Form.Label htmlFor="entry-point">SAML Entry Point</Form.Label>
              <Input id="entry-point" placeholder="https://example.okta.com/app/sso/saml" />
            </Form.Field>
            <Form.Field>
              <Form.Label htmlFor="certificate">X509 Certificate</Form.Label>
              <Input id="certificate" placeholder="Paste certificate PEM" />
            </Form.Field>
            <Form.Field>
              <Form.Label htmlFor="force-auth">Force re-authentication</Form.Label>
              <Switch id="force-auth" checked={false} readOnly />
            </Form.Field>
            <Typography variant="body.small" color="neutral">
              This form captures configuration data only. Persistence and validation will be wired in
              Phase 2.
            </Typography>
          </Stack>
        </Form>
      </Card>
    </Box>
  );
};

export default SsoPage;
