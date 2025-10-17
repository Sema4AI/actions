import { Box, Card, Header, Link, Typography } from '@sema4ai/components';
import { IconBook } from '@sema4ai/icons';

const KnowledgeBasePage = () => {
  return (
    <Box padding="$32" display="flex" flexDirection="column" gap="$24">
      <Header>
        <Header.Title title="Knowledge Base" icon={IconBook} />
        <Header.Description>
          Curate internal knowledge articles and share curated playbooks with your organization.
        </Header.Description>
      </Header>
      <Card>
        <Typography variant="body.large">
          This is enterprise-only scaffolding. The backend APIs for authoring and indexing knowledge
          articles will ship in feature plan <strong>004-backend-enterprise-features</strong>.
        </Typography>
      </Card>
      <Card>
        <Typography variant="body.default" color="neutral">
          Need early access?{' '}
          <Link href="https://sema4.ai/contact" target="_blank">
            Contact the Sema4.ai team
          </Link>{' '}
          to join the preview program.
        </Typography>
      </Card>
    </Box>
  );
};

export default KnowledgeBasePage;
