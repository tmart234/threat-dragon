import providers, { getDisplayName } from '@/service/providers.js';
import sessionProvider from '@/service/session.provider.js';

describe('service/providers.js', () => {
    describe('providerNames', () => {
        it('is an object', () => {
            expect(providers.providerNames).toBeInstanceOf(Object);
        });

        it('has a github provider', () => {
            expect(providers.providerNames.github).toEqual('github');
        });

        it('has a local provider', () => {
            expect(providers.providerNames.local).toEqual('local');
        });

        it('prevents mutations', () => {
            expect(() => {
                providers.providerNames.github = 'foobar';
            }).toThrowError('Cannot assign to read only property');
        });
    });

    describe('allProviders', () => {
        it('is an object', () => {
            expect(providers.allProviders).toBeInstanceOf(Object);
        });

        it('has a github provider', () => {
            expect(providers.allProviders.github.key).toEqual('github');
        });

        it('has a local provider', () => {
            expect(providers.allProviders.local.key).toEqual('local');
        });

        it('prevents mutations', () => {
            expect(() => {
                providers.allProviders.github = { foo: 'bar' };
            }).toThrowError('Cannot assign to read only property');
        });
    });

    describe('getDashboardActions', () => {
        it('throws an error for an unknown provider', () => {
            const provider = 'fake';
            expect(() => {
                providers.getDashboardActions(provider);
            }).toThrowError(`Unknown provider: ${provider}`);
        });

        it('gets the github provider dashboard actions', () => {
            const actual = providers.getDashboardActions(providers.providerNames.github);
            expect(actual.length).toBeGreaterThan(0);
        });

        it('gets the local provider dashboard actions', () => {
            const actual = providers.getDashboardActions(providers.providerNames.local);
            expect(actual.length).toBeGreaterThan(0);
        });

        it('throws an error when no actions are configured', () => {
            sessionProvider.getDashboardActions = jest.fn();
            expect(() => {
                providers.getDashboardActions(providers.providerNames.local);
            }).toThrowError(`No dashboard actions configured`);
        });
    });

    describe('getDisplayName', () => {
        it('gets the display name of a provider', () => {
            expect(getDisplayName('github')).toEqual('GitHub');
        });
    });
});