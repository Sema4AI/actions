import React, { useState } from 'react';
import { Box, Card, Button, Text, List, ListItem } from '@sema4ai/components';
import { RobotRunInputModal } from './RobotRunInputModal';
import { useRunRobotTask } from '~/queries/robots';
import type { RobotPackageDetailAPI } from '~/lib/types';

interface RobotPackageDisplayProps {
  robot: RobotPackageDetailAPI;
}

export const RobotPackageDisplay: React.FC<RobotPackageDisplayProps> = ({ robot }) => {
  const [modalOpen, setModalOpen] = useState(false);
  const [selectedTask, setSelectedTask] = useState<string | null>(null);
  const runRobotTask = useRunRobotTask();

  const handleRunClick = (taskName: string) => {
    setSelectedTask(taskName);
    setModalOpen(true);
  };

  const handleModalClose = () => {
    setModalOpen(false);
    setSelectedTask(null);
  };

  const handleModalSubmit = (inputs: Record<string, string>) => {
    if (!selectedTask) return;
    runRobotTask.mutate({
      robot_package_path: robot.path,
      task_name: selectedTask,
      inputs,
      use_secrets: false,
    });
    setModalOpen(false);
    setSelectedTask(null);
  };

  return (
    <Card mb={24} p={24}>
      <Box mb={8}>
        <Text as="h2" fontSize={20} fontWeight={600} mb={4}>
          {robot.name}
        </Text>
        {robot.description && (
          <Text color="content.subtle" mb={4}>
            {robot.description}
          </Text>
        )}
        <Text fontSize={14} color="content.subtle">
          <b>Path:</b> {robot.path}
        </Text>
        <Text fontSize={14} color="content.subtle">
          <b>Environment Hash:</b> {robot.environment_hash}
        </Text>
      </Box>
      <Box mt={16}>
        <Text as="h3" fontSize={16} fontWeight={500} mb={8}>
          Tasks
        </Text>
        <List>
          {robot.tasks.map((task) => (
            <ListItem key={task.name} mb={8}>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Text fontWeight={500}>{task.name}</Text>
                  <Text fontSize={13} color="content.subtle">{task.docs}</Text>
                </Box>
                <Button
                  size="xs"
                  variant="primary"
                  onClick={() => handleRunClick(task.name)}
                  loading={runRobotTask.isPending && selectedTask === task.name}
                >
                  Run
                </Button>
              </Box>
            </ListItem>
          ))}
        </List>
      </Box>
      <RobotRunInputModal
        isOpen={modalOpen}
        onClose={handleModalClose}
        onSubmit={handleModalSubmit}
        robotName={robot.name}
        taskName={selectedTask || ''}
      />
    </Card>
  );
};
