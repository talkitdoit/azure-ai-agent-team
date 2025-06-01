using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.Azure.Management.ResourceManager;
using Microsoft.Azure.Management.ResourceManager.Models;
using Microsoft.Rest.Azure;

namespace AzureResourceManagement
{
    public class AzureResourceService
    {
        private readonly ResourceManagementClient _resourceClient;

        public AzureResourceService(ResourceManagementClient resourceClient)
        {
            _resourceClient = resourceClient ?? throw new ArgumentNullException(nameof(resourceClient));
        }

        public async Task<IEnumerable<ResourceGroup>> GetResourceGroupsAsync()
        {
            var resourceGroups = new List<ResourceGroup>();
            var response = await _resourceClient.ResourceGroups.ListAsync();
            
            resourceGroups.AddRange(response);
            
            while (!string.IsNullOrEmpty(response.NextPageLink))
            {
                response = await _resourceClient.ResourceGroups.ListNextAsync(response.NextPageLink);
                resourceGroups.AddRange(response);
            }

            return resourceGroups;
        }

        public async Task<ResourceGroup> CreateResourceGroupAsync(string name, string location, Dictionary<string, string> tags = null)
        {
            var parameters = new ResourceGroup
            {
                Location = location,
                Tags = tags ?? new Dictionary<string, string>
                {
                    { "Environment", "Development" },
                    { "ManagedBy", "AzureResourceService" }
                }
            };

            return await _resourceClient.ResourceGroups.CreateOrUpdateAsync(name, parameters);
        }

        public async Task DeleteResourceGroupAsync(string name)
        {
            try
            {
                await _resourceClient.ResourceGroups.DeleteAsync(name);
            }
            catch (CloudException ex) when (ex.Response.StatusCode == System.Net.HttpStatusCode.NotFound)
            {
                // Resource group already deleted or doesn't exist
                Console.WriteLine($"Resource group {name} not found.");
            }
        }
    }
}