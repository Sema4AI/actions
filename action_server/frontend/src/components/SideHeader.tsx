import { FC, useCallback } from 'react';
import { Box, Typography, usePopover } from '@sema4ai/components';
import { IconGlobe, IconLink, IconWifiNoConnection } from '@sema4ai/icons';
import { styled } from '~/vendor/sema4ai-theme';

import { useActionServerContext } from '~/lib/actionServerContext';
import { ActionServerLogo } from './Logo';
import { InputCopy } from './CopyToClipboard';

const Container = styled(Box)`
  cursor: pointer;
`;

const EMPTY = '';

const ExposedIcon = styled(Box)<{ $enabled: boolean }>`
  position: relative;
  width: ${({ theme }) => theme.sizes.$24};
  height: ${({ theme }) => theme.sizes.$24};

  &::after {
    display: ${({ $enabled }) => ($enabled ? 'none' : 'block')};
    position: absolute;
    content: '';
    left: 50%;
    top: 0;
    width: 2px;
    height: 100%;
    background: currentColor;
    border-radius: 2px;
    transform: rotate(-45deg);
  }

  > svg {
    display: block;
  }
`;

export const SideHeader: FC = () => {
  const { loadedServerConfig } = useActionServerContext();

  const { referenceRef, referenceProps, PopoverContent, setOpen } = usePopover({
    placement: 'right',
    width: 440,
    offset: 0,
  });

  const onMouseOver = useCallback(() => {
    setOpen(true);
  }, []);

  const onMouseLeave = useCallback(() => {
    setOpen(false);
  }, []);

  const exposeUrl: string = loadedServerConfig.data?.expose_url || EMPTY;
  const isExposed: boolean = loadedServerConfig.isPending ? false : exposeUrl !== EMPTY;
  const isConfigAvailable: boolean = loadedServerConfig.data !== undefined;

  return (
    <Box onMouseLeave={onMouseLeave}>
      <Container
        ref={referenceRef}
        {...referenceProps}
        display="flex"
        alignItems="center"
        gap="$8"
        height="$32"
        mb="$48"
        px="$8"
        onMouseOver={onMouseOver}
      >
        <Box
          display="flex"
          borderRadius="$8"
          width="$32"
          height="$32"
          backgroundColor="blue70"
          alignItems="center"
          justifyContent="center"
        >
          <ActionServerLogo size={20} />
        </Box>
        <Typography fontWeight={600}>Action Server</Typography>
        <ExposedIcon $enabled={isExposed} ml="auto">
          {isConfigAvailable ? (
            <IconGlobe size={24} />
          ) : (
            <IconWifiNoConnection size={24} color="content.error" />
          )}
        </ExposedIcon>
      </Container>
      <PopoverContent>
        <Box p="$16" backgroundColor="background.primary" borderRadius="$8" boxShadow="medium">
          {!isConfigAvailable && (
            <Typography fontWeight="bold" mb="$16">
              Action Server Config unavailable (the network is currently down or the Action Server
              was stopped).
            </Typography>
          )}

          {isConfigAvailable && isExposed && (
            <>
              <Typography fontWeight="bold" mb="$16">
                Action Server exposed
              </Typography>
              <Box mb="$16">
                <InputCopy iconLeft={IconLink} label="Server URL" value={exposeUrl} readOnly />
              </Box>
            </>
          )}

          {isConfigAvailable && !isExposed && (
            <>
              <Typography fontWeight="bold" mb="$16">
                Action Server not exposed
              </Typography>
              <Typography lineHeight="$16" mb="$12">
                To serve a public URL for your Action Server, start it with the{' '}
                <Typography as="span" color="content.accent">
                  --expose
                </Typography>{' '}
                parameter set.
              </Typography>
              <InputCopy
                aria-label="Expose command"
                value="action-server start --expose"
                readOnly
              />
            </>
          )}
        </Box>
      </PopoverContent>
    </Box>
  );
};
