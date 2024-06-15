import { Button, Dialog } from '@robocorp/components';
import { FC } from 'react';

export const ErrorLogin: FC<{ errorTitle: string; errorMessage: string; clearError: any }> = ({
  errorTitle,
  errorMessage,
  clearError,
}) => {
  return (
    <Dialog
      open={true}
      onClose={() => {
        clearError();
      }}
      size="medium"
    >
      <Dialog.Header>
        <Dialog.Header.Description>{errorTitle}</Dialog.Header.Description>
      </Dialog.Header>
      <Dialog.Content>{errorMessage}</Dialog.Content>
      <Dialog.Actions>
        <Button
          onClick={() => {
            clearError();
          }}
          variant="primary"
        >
          Close
        </Button>
      </Dialog.Actions>
    </Dialog>
  );
};
