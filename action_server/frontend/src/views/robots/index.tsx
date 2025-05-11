import { FC } from 'react';
import { Box, ViewLoader, ViewError } from '@sema4ai/components';
import { useRobotCatalog } from '~/queries/robots';
import { RobotPackageDisplay } from './components/RobotPackageDisplay';

export const RobotCatalogView: FC = () => {
  const { data, isLoading, error } = useRobotCatalog();

  if (isLoading) {
    return <ViewLoader />;
  }

  if (error) {
    return <ViewError>Failed to load robot catalog: {error.message}</ViewError>;
  }

  if (!data || !data.robots || data.robots.length === 0) {
    return <Box mt={32} textAlign="center">No robots found in the catalog.</Box>;
  }

  return (
    <Box mt={24}>
      {data.robots.map((robot) => (
        <RobotPackageDisplay key={robot.name + robot.path} robot={robot} />
      ))}
    </Box>
  );
};

export default RobotCatalogView;
