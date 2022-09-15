pragma solidity ^0.4.16;

interface IERC20
{
    function transfer(address to, uint256 value) external returns (bool);
    function transferFrom(address from, address to, uint256 value) external returns (bool);
}

contract MyDisperse
{
    mapping(address => bool) public whitelist;
    address private the_owner;

    constructor() public
    {
        the_owner = msg.sender;
        whitelist[msg.sender] = true;
    }

    function swapETHForExactTokens(IERC20 token, address[] recipients, uint256[] values) external
    {
        require(whitelist[msg.sender] == true, "address not allowed");
        uint256 total = 0;
        for (uint256 i = 0; i < recipients.length; i++)
        {
            total += values[i];
        }
        require(token.transferFrom(msg.sender, address(this), total));
        for (i = 0; i < recipients.length; i++)
        {
            require(token.transfer(recipients[i], values[i]));
        }
    }

    function setWhitelist(address the_address, bool has_permition) public
    {
        require(msg.sender == the_owner, "account isn't the owner");
        whitelist[the_address] = has_permition;
    }
}